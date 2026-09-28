# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

import os
import certifi
import sys
import time
import multiprocessing
from multiprocessing import Process, Queue

from PySide6.QtGui import QPalette, QColor, Qt, QPixmap, QFont, QIcon, QPainter
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QProgressBar, \
    QStyleFactory, QSplashScreen
from PySide6.QtCore import QTimer, Slot

from simulator.Message import MessageType, Message
from simulator.model.ModelConfig import get_default_config
from simulator.model.ModelController import run_simulator
from simulator.ui.MainDisplayPanel import MainDisplayPanel

SATELLITE_EMOJI = "🛰️"


class MainWindow(QMainWindow):
    def __init__(self, msg_queue_in: Queue, msg_queue_out: Queue):
        """
        MainWindow constructor: initializes inter-process messaging queues and creates the main panel
        :param msg_queue_in: for messages coming into the window process
        :param msg_queue_out: for messages going to the simulation process
        """
        super().__init__()
        self.msg_queue_in = msg_queue_in  # Queue to read from simulator
        self.msg_queue_out = msg_queue_out  # Queue to send commands to simulator
        self.config = get_default_config()
        self.main_panel = MainDisplayPanel( msg_queue_out, msg_queue_in, self.config )
        self.setCentralWidget(self.main_panel)

        self.setWindowTitle("Cubesat Simulator")
        self.resize(1600, 1000)

        self.queue_timer = QTimer(self)
        self.queue_timer.timeout.connect(self.check_queue)
        self.queue_timer.start(50)  # Poll every 50ms

    @Slot()
    def check_queue(self) -> None:
        """
        Method to poll the queue and handle any incoming messages
        :return: None
        """
        if not self.msg_queue_in.empty():
            msg = self.msg_queue_in.get()
            self.handle_message(msg)

    @Slot(object)
    def handle_message(self, msg: Message) -> None:
        """
        Message handling method, dispatching incoming messages for the window process
        :param msg: the message to handle
        :return:
        """
        if msg.type == MessageType.STATUS_LOG_MESSAGE:
            if len(msg.data) < 250:
                self.main_panel.status_panel.set_text(msg.data)
            self.main_panel.log_panel.append_message(msg.data)
        elif msg.type == MessageType.STATUS_SIMULATION_UPDATE:
            self.main_panel.status_panel.set_progress(msg.data)
        elif msg.type == MessageType.STATUS_SIMULATION_COMPLETE:
            self.main_panel.update_results(msg.data)
            self.main_panel.status_panel.play_button.setEnabled(True)
            self.main_panel.status_panel.duration_field.setEnabled(True)
            self.main_panel.status_panel.step_size_field.setEnabled(True)
            self.main_panel.status_panel.datetime_picker.setEnabled(True)

    def closeEvent(self, event) -> None:
        """
        Method to handle the close event
        :param event:
        :return:
        """
        self.msg_queue_out.put(Message(MessageType.CMD_SHUTDOWN_SIMULATOR))
        event.accept()


def run_gui_process(q_in: Queue, q_out: Queue) -> None:
    """
    Function to start the user interface process
    :param q_in: queue for messages incoming to the gui process
    :param q_out: queue for message outgoing from the gui process
    :return:
    """
    app = QApplication(sys.argv)

    # pixmap = QPixmap("../resources/Splash.png")  # path to your image
    # splash = QSplashScreen(pixmap)
    # splash.setFont(QFont("Arial", 12))
    # splash.showMessage("Starting simulator...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
    # splash.show()
    # QTimer.singleShot(2500, splash.close)  # close after 2.5s

    icon = create_emoji_icon(SATELLITE_EMOJI)
    app.setApplicationName("CubeSat Simulator")
    app.setApplicationDisplayName("CubeSat Simulator")

    app.setWindowIcon(icon)  # applies to dock on macOS
    set_dark_theme(app)  # Apply the dark theme
    window = MainWindow(msg_queue_in=q_in, msg_queue_out=q_out)
    # splash.finish(window)
    window.show()
    sys.exit(app.exec())


def run_simulation_process(q_in: Queue, q_out: Queue) -> None:
    """
    Function to start the simulation process
    :param q_in: queue for messages incoming to the simulation process
    :param q_out: queue for message outgoing from the simulation process
    :return:
    """
    running = True
    q_out.put(Message(MessageType.STATUS_LOG_MESSAGE, "Simulation environment started"))

    while running:
        # Check for incoming commands from the GUI
        if not q_in.empty():
            cmd = q_in.get()
            if cmd.type == MessageType.CMD_START_SIMULATION:
                run_simulator(cmd.data, q_out)
            elif cmd.type == MessageType.CMD_SHUTDOWN_SIMULATOR:
                running = False
                break

        time.sleep(0.1)

    q_out.put(Message(MessageType.STATUS_LOG_MESSAGE, "Simulation Finished"))


def set_dark_theme(app: QApplication):
    """
    Function to create a dark theme
    :param app:
    :return:
    """
    app.setStyle(QStyleFactory.create("Fusion"))
    dark_palette = QPalette()

    # Define dark colors
    dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.WindowText, Qt.white)
    dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
    dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
    dark_palette.setColor(QPalette.ToolTipText, Qt.white)
    dark_palette.setColor(QPalette.Text, Qt.white)
    dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
    dark_palette.setColor(QPalette.ButtonText, Qt.white)
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    dark_palette.setColor(QPalette.HighlightedText, Qt.black)

    app.setPalette(dark_palette)
    app.setStyleSheet("QToolTip { color: #ffffff; background-color: #353535; border: 1px solid #ffffff; }")


def create_emoji_icon(emoji: str, size: int = 256) -> QIcon:
    """
    Render a Unicode emoji into a QIcon.
    :param emoji:
    :param size:
    :return:
    """
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    font = QFont("Apple Color Emoji", int(size * 0.8))
    font.setStyleStrategy(QFont.PreferAntialias)
    painter.setFont(font)

    # Center the emoji
    rect = pixmap.rect()
    painter.drawText(rect, Qt.AlignCenter, emoji)
    painter.end()

    return QIcon(pixmap)


def main():
    """
    Main method for starting the application
    :return:
    """
    os.environ['SSL_CERT_FILE'] = certifi.where()
    # Must use 'spawn' start method for PySide6/multiprocessing compatibility
    multiprocessing.set_start_method('spawn', force=True)

    # Queues:
    # gui_to_sim: GUI puts commands here, Sim reads from here
    # sim_to_gui: Sim puts updates here, GUI reads from here
    gui_to_sim_queue = Queue()
    sim_to_gui_queue = Queue()

    # Create processes
    p_gui = Process(target=run_gui_process, args=(sim_to_gui_queue, gui_to_sim_queue))
    p_sim = Process(target=run_simulation_process, args=(gui_to_sim_queue, sim_to_gui_queue))

    # Start them
    p_sim.start()  # Start simulator first
    p_gui.start()  # Then start the GUI

    # Wait for the GUI process to close before the main program exits
    p_gui.join()
    p_sim.join()  # Ensure simulator process closes gracefully too

    print("All processes finished.")


# Start the application
if __name__ == "__main__":
    main()

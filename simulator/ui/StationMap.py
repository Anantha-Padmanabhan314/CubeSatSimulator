# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

from PySide6.QtCore import QPoint
from PySide6.QtWidgets import QWidget, QVBoxLayout, QToolTip
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import cartopy.feature as cfeature
import cartopy.crs as ccrs

from simulator.ui.GroundTrackPanel import BG_COLOR
import cartopy.io.shapereader as shpreader


class StationMap(QWidget):
    """
    A global map-based widget for graphically selecting SatNOGS ground stations for use in the simulation
    """
    def __init__(self, stations, on_station_selected, selected_station_ids=None, parent=None):
        """
        A constructor for the StationMap
        :param stations: The list of all currently available (may be filtered) stations for possible selection
        :param on_station_selected: a callback method to call when a station is selected
        :param selected_station_ids: a set of initially selected stations
        :param parent:
        """
        super().__init__(parent)
        self.stations = stations
        self.on_station_selected = on_station_selected
        self.selected_station_ids = set(str(x) for x in (selected_station_ids or []))

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Matplotlib figure + canvas
        self.figure = Figure(facecolor=BG_COLOR)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
        self.layout.addWidget(self.canvas)

        # Station data
        self._station_artists = {}
        self._station_positions = {}
        self._hovered_sid = None
        self._original_size = 2
        self._hover_size = 6
        self._colors = {
            "available": "red",
            "selected": "lime",
            "hover": "yellow"
        }

        # --- PAN/ZOOM state ---
        self._dragging = False
        self._last_mouse_pos = None

        self.setup_map()
        self.draw_stations()

        # Events
        self.canvas.mpl_connect("button_press_event", self._start_pan)
        self.canvas.mpl_connect("button_release_event", self._end_pan)
        self.canvas.mpl_connect("motion_notify_event", self._mouse_move)
        self.canvas.mpl_connect("scroll_event", self._zoom)

        # Original events
        self.canvas.mpl_connect("button_press_event", self.handle_click)
        self.canvas.mpl_connect("motion_notify_event", self.handle_hover)
        self.canvas.mpl_connect("figure_leave_event", lambda e: self._clear_hover())

        self.figure.subplots_adjust(left=0.03, right=0.97, top=0.98, bottom=0.02)

    def setup_map(self) -> None:
        """
        Sets up the map
        :return:
        """
        self.ax.set_global()
        self.ax.add_feature(cfeature.LAND, color='black')
        self.ax.add_feature(cfeature.COASTLINE, linewidth=0.5, edgecolor='gray')
        self.ax.add_feature(cfeature.BORDERS, linestyle=':', edgecolor='gray')
        self.ax.add_feature(cfeature.OCEAN, color='darkblue', alpha=0.5)

        # --- Country labels ---
        shp = shpreader.natural_earth("110m", "cultural", "admin_0_countries")
        reader = shpreader.Reader(shp)

        for rec in reader.records():
            name = rec.attributes.get("NAME_LONG")
            if not name:
                continue
            try:
                c = rec.geometry.centroid
                if abs(c.y) < 85:
                    self.ax.text(
                        c.x, c.y, name,
                        fontsize=6, color="white",
                        ha="center", va="center",
                        transform=ccrs.PlateCarree(),
                        alpha=0.7, zorder=5
                    )
            except:
                pass

        gl = self.ax.gridlines(draw_labels=True, linestyle='--', alpha=0.5)
        gl.top_labels = False
        gl.right_labels = False

        self.ax.set_title("SatNOGS Stations")


    def draw_stations(self) -> None:
        """
        Draw the available and selected stations on the map
        :return:
        """
        for s in self.stations:
            sid = str(s["id"])
            try:
                lat = float(s["lat"])
                lon = float(s["lng"])
            except:
                continue

            self._station_positions[sid] = (lat, lon)
            color = self._colors["selected"] if sid in self.selected_station_ids else self._colors["available"]

            artist = self.ax.plot(
                lon, lat,
                marker="o",
                markersize=self._original_size,
                color=color,
                transform=ccrs.PlateCarree(),
                zorder=10,
                picker=5
            )[0]

            self._station_artists[sid] = artist

        self.canvas.draw_idle()

    def _start_pan(self, event) -> None:
        """
        Method to capture the start-of-pan event
        :param event:
        :return:
        """
        if event.button == 3:  # Right mouse holds = pan
            self._dragging = True
            self._last_mouse_pos = (event.x, event.y)

    def _end_pan(self, event) -> None:
        """
        Method to capture the end-of-pan event
        :param event:
        :return:
        """
        if event.button == 3:
            self._dragging = False
            self._last_mouse_pos = None

    def _mouse_move(self, event) -> None:
        """
        Method to capture the mouse move event
        :param event:
        :return:
        """
        if not self._dragging or event.inaxes != self.ax:
            return

        dx = event.x - self._last_mouse_pos[0]
        dy = event.y - self._last_mouse_pos[1]
        self._last_mouse_pos = (event.x, event.y)

        # Convert pixel drag to axis movement
        x0, x1 = self.ax.get_xlim()
        y0, y1 = self.ax.get_ylim()

        width = x1 - x0
        height = y1 - y0

        # Move opposite to drag direction
        factor = 0.005
        self.ax.set_xlim(x0 - dx * factor, x1 - dx * factor)
        self.ax.set_ylim(y0 + dy * factor, y1 + dy * factor)

        self.canvas.draw_idle()

    def _zoom(self, event) -> None:
        """
        Method to capture the zoome event
        :param event:
        :return:
        """
        if event.inaxes != self.ax:
            return

        scale = 1.2 if event.button == "down" else 1/1.2
        x0, x1 = self.ax.get_xlim()
        y0, y1 = self.ax.get_ylim()

        cx, cy = event.xdata, event.ydata

        # Zoom relative to cursor
        self.ax.set_xlim(cx + (x0 - cx) * scale, cx + (x1 - cx) * scale)
        self.ax.set_ylim(cy + (y0 - cy) * scale, cy + (y1 - cy) * scale)

        self.canvas.draw_idle()

    def handle_click(self, event) -> None:
        """
        Method to capture a mouse click event
        :param event:
        :return:
        """
        if event.button == 3:
            return  # ignore right-clicks (reserved for pan)

        if event.inaxes != self.ax:
            return

        lon_clicked = event.xdata
        lat_clicked = event.ydata
        if lon_clicked is None:
            return

        best_sid, bestd = None, float("inf")
        for sid, (lat, lon) in self._station_positions.items():
            dlat = lat_clicked - lat
            dlon = lon_clicked - lon
            d = dlat*dlat + dlon*dlon
            if d < bestd:
                best_sid = sid
                bestd = d

        if best_sid is None:
            return

        station = next((s for s in self.stations if str(s["id"]) == best_sid), None)
        if not station:
            return

        if best_sid in self.selected_station_ids:
            self.selected_station_ids.remove(best_sid)
            self._station_artists[best_sid].set_color(self._colors["available"])
        else:
            self.selected_station_ids.add(best_sid)
            self._station_artists[best_sid].set_color(self._colors["selected"])

        self.canvas.draw_idle()
        self.on_station_selected(best_sid, station)

    def handle_hover(self, event) -> None:
        """
        Method to capture the mouse-hover event
        :param event:
        :return:
        """
        if event.inaxes != self.ax or self._dragging:
            self._clear_hover()
            return

        lon = event.xdata
        lat = event.ydata
        if lon is None:
            self._clear_hover()
            return

        best_sid, bestd = None, float("inf")
        for sid, (slat, slon) in self._station_positions.items():
            d = (lat - slat)**2 + (lon - slon)**2
            if d < bestd:
                best_sid, bestd = sid, d

        if best_sid is None or best_sid == self._hovered_sid:
            return

        self._clear_hover()

        self._hovered_sid = best_sid
        artist = self._station_artists[best_sid]
        artist.set_color(self._colors["hover"])
        artist.set_markersize(self._hover_size)

        # Tooltip
        x_disp, y_disp = self.ax.transData.transform(
            (self._station_positions[best_sid][1], self._station_positions[best_sid][0])
        )
        canvas_x = int(x_disp / self.figure.dpi * self.canvas.width() / self.figure.get_size_inches()[0])
        canvas_y = int(self.canvas.height() - (y_disp / self.figure.dpi * self.canvas.height() / self.figure.get_size_inches()[1]))
        global_point = self.canvas.mapToGlobal(QPoint(canvas_x + 10, canvas_y - 20))

        station_obj = next((s for s in self.stations if str(s["id"]) == best_sid), None)
        if station_obj:
            QToolTip.showText(global_point, station_obj.get("name", "Unknown"), self.canvas)

        self.canvas.draw_idle()

    def _clear_hover(self) -> None:
        """
        Method to capture the clear hover event
        :return:
        """
        if self._hovered_sid:
            artist = self._station_artists.get(self._hovered_sid)
            if artist:
                color = self._colors["selected"] if self._hovered_sid in self.selected_station_ids else self._colors["available"]
                artist.set_color(color)
                artist.set_markersize(self._original_size)
        self._hovered_sid = None
        QToolTip.hideText()
        self.canvas.draw_idle()

    def update_stations(self, stations, selected_station_ids=None) -> None:
        """
        Method to update stations based on updated selection
        :param stations:
        :param selected_station_ids:
        :return:
        """
        self.stations = stations

        if selected_station_ids is not None:
            self.selected_station_ids = set(str(x) for x in selected_station_ids)

        for artist in self._station_artists.values():
            artist.remove()

        self._station_artists.clear()
        self._station_positions.clear()
        self._hovered_sid = None

        self.draw_stations()
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()

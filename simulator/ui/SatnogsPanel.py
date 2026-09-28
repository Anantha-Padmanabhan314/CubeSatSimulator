# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Adrian Payne
#
# This file is part of the SpacecraftSimulator project.
# The full license text can be found in the LICENSE.txt file at the project root.

import requests
from math import ceil

from PySide6.QtCore import (
    Qt, QSize, QAbstractListModel, QModelIndex, QByteArray,
    QMimeData, QThreadPool, QRunnable, Signal, QObject, Slot
)
from PySide6.QtGui import QPixmap, QPainter, QFontMetrics, QFont
from PySide6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QListView,
    QLabel, QComboBox, QSpinBox, QPushButton, QHBoxLayout, QSizePolicy,
    QStyledItemDelegate, QStyleOptionViewItem, QStyle, QMessageBox, QTabWidget
)

from simulator.model.subsystems.ground.GroundConfig import GroundConfigType
from simulator.ui.StationMap import StationMap

# ------------------- Config -------------------
API_URL = "https://network.satnogs.org/api/stations/"
PAGE_SIZE = 20
IMAGE_TIMEOUT = 8  # seconds
MIME_STATION_ID = "application/x-station-id"

def fetch_json(url, timeout=30):
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("Failed to fetch JSON:", e)
        return []

# ------------------- Image Loader (threaded) -------------------
class ImageSignals(QObject):
    finished = Signal(str, QPixmap)  # url, pixmap

class ImageFetchRunnable(QRunnable):
    def __init__(self, url, signals):
        super().__init__()
        self.url = url
        self.signals = signals

    def run(self):
        try:
            r = requests.get(self.url, timeout=IMAGE_TIMEOUT)
            r.raise_for_status()
            data = r.content
            pix = QPixmap()
            if pix.loadFromData(data):
                # scale to a reasonable thumbnail size here if desired later
                self.signals.finished.emit(self.url, pix)
                return
        except Exception:
            pass
        # emit an empty pixmap on failure so delegates can show placeholder
        self.signals.finished.emit(self.url, QPixmap())

# ------------------- Image Cache -------------------
class ImageCache(QObject):
    image_loaded = Signal(str)  # url

    def __init__(self):
        super().__init__()
        self._cache = {}  # url -> QPixmap (may be null QPixmap on fail)
        self._loading = set()
        self._pool = QThreadPool.globalInstance()
        self._signals = ImageSignals()
        self._signals.finished.connect(self._on_finished)

    def get(self, url):
        return self._cache.get(url)

    def ensure_loaded(self, url):
        if not url:
            return
        if url in self._cache:
            return
        if url in self._loading:
            return
        # schedule fetch
        self._loading.add(url)
        self._pool.start(ImageFetchRunnable(url, self._signals))

    @Slot(str, QPixmap)
    def _on_finished(self, url, pixmap):
        self._cache[url] = pixmap
        self._loading.discard(url)
        self.image_loaded.emit(url)

# ------------------- Station Model -------------------
class StationListModel(QAbstractListModel):
    """
    Model containing a list of station dicts.
    Exposes filtered/paginated view via provided API on the model (set_filter, set_page)
    """
    def __init__(self, stations=None, image_cache=None):
        """
        Constructor for the StationListModel, based on the passed in set of stations
        :param stations:
        :param image_cache:
        """
        super().__init__()
        self._all = stations or []       # original dataset (list of dict)
        self._filtered = list(self._all) # filtered subset
        self._page = 0
        self._page_size = PAGE_SIZE
        self._image_cache = image_cache or ImageCache()
        self._current_band = "VHF"
        self._current_status = "Active"
        self._apply_filters = True

        # precompute bands and statuses for speed
        for s in self._all:
            s['_bands'] = sorted({a.get('band') for a in s.get('antenna', []) if a.get('band')})
            s['_status'] = s.get('status') or "Unknown"

    def rowCount(self, parent=QModelIndex()):
        return len(self.current_page_items())

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        station = self.current_page_items()[index.row()]
        if role == Qt.DisplayRole:
            return station.get('name', 'Unknown')
        if role == Qt.UserRole:
            return station
        return None

    def flags(self, index):
        base = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled
        return base

    # --- pagination/filtering APIs ---
    def current_page_items(self):
        start = self._page * self._page_size
        end = start + self._page_size
        return self._filtered[start:end]

    def total_pages(self):
        return max(1, ceil(len(self._filtered) / self._page_size))

    def set_page(self, page):
        page = max(0, min(page, self.total_pages() - 1))
        if page == self._page:
            return
        self.beginResetModel()
        self._page = page
        self.endResetModel()

    def set_page_size(self, n):
        if n <= 0:
            return
        self._page_size = n
        self.set_page(0)

    def set_filter(self, band=None, status=None, rebuild_filtered=True):
        self._current_band = band or "All"
        self._current_status = status or "All"

        if not self._apply_filters:
            # Selected model never filters. Always show all.
            self._filtered = list(self._all)
            self._page = 0
            self.layoutChanged.emit()
            return

        if rebuild_filtered:
            fl = []
            for s in self._all:
                ok_band = (self._current_band == "All") or (self._current_band in s['_bands'])
                ok_status = (self._current_status == "All") or (s['_status'] == self._current_status)
                if ok_band and ok_status:
                    fl.append(s)
            self._filtered = fl
            self._page = 0
            self.layoutChanged.emit()

    def rebuild_filtered(self):
        if not self._apply_filters:
            self._filtered = list(self._all)
            self.layoutChanged.emit()
            return
        self.set_filter(self._current_band, self._current_status)

    def get_station_by_id(self, sid):
        # stations may not have numeric id - we use str(station['id'])
        for s in self._all:
            if str(s.get('id')) == str(sid):
                return s
        return None

    # --- drag & drop MIME handling at model level (for export only) ---
    def mimeTypes(self):
        return [MIME_STATION_ID]

    def mimeData(self, indexes):
        md = QMimeData()
        if not indexes:
            return md
        # Use the absolute station id of the selected item (from the current page)
        st = self.current_page_items()[indexes[0].row()]
        sid = str(st.get('id'))
        md.setData(MIME_STATION_ID, QByteArray(sid.encode('utf-8')))
        return md

# ------------------- Delegate (paints items) -------------------
class StationDelegate(QStyledItemDelegate):
    """
    Paints compact station card look — uses image cache for thumbnails.
    """
    def __init__(self, image_cache, parent=None):
        super().__init__(parent)
        self.img_cache = image_cache
        self.img_cache.image_loaded.connect(self.on_image_loaded)
        self.thumb_size = QSize(96, 64)
        self.margin = 6
        self.row_height = max(self.thumb_size.height() + 2*self.margin, 96)

    @Slot(str)
    def on_image_loaded(self, url):
        # Entire view will update; could be optimized to update only rows that referenced the url
        parent = self.parent()
        if parent:
            parent.viewport().update()

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), self.row_height)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        station = index.data(Qt.UserRole)
        if station is None:
            return
        painter.save()

        # background (selected highlight)
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
            text_pen = option.palette.highlightedText().color()
        else:
            painter.fillRect(option.rect, option.palette.base())
            text_pen = option.palette.text().color()

        # draw thumbnail area
        x = option.rect.x() + self.margin
        y = option.rect.y() + self.margin
        thumb_rect = option.rect.adjusted(self.margin, self.margin,
                                          -option.rect.width() + self.thumb_size.width() + self.margin,
                                          -option.rect.height() + self.thumb_size.height() + self.margin)
        # fetch image from cache or trigger load
        image_url = station.get('image')
        pix = None
        if image_url:
            pix = self.img_cache.get(image_url)
            if pix is None:
                # schedule load, show placeholder for now
                self.img_cache.ensure_loaded(image_url)

        if pix and not pix.isNull():
            scaled = pix.scaled(self.thumb_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.drawPixmap(x, y, scaled)
        else:
            # placeholder rectangle
            painter.setPen(Qt.NoPen)
            painter.setBrush(option.palette.mid())
            painter.drawRect(x, y, self.thumb_size.width(), self.thumb_size.height())

        # draw text block right of thumbnail
        text_x = x + self.thumb_size.width() + self.margin
        text_w = option.rect.width() - (self.thumb_size.width() + 3*self.margin)
        tx = text_x
        ty = y

        # Name (bold)
        name = station.get('name', 'Unnamed')
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        fm = QFontMetrics(font)
        painter.setPen(text_pen)
        painter.drawText(tx, ty + fm.ascent(), fm.elidedText(name, Qt.ElideRight, text_w))

        # Status & bands on next line
        font.setBold(False)
        painter.setFont(font)
        fm = QFontMetrics(font)
        sstatus = station.get('_status', 'Unknown')
        bands = ", ".join(station.get('_bands') or [])
        line2 = f"Status: {sstatus}  Bands: {bands or 'N/A'}"
        painter.drawText(tx, ty + fm.height() + 6 + fm.ascent(), fm.elidedText(line2, Qt.ElideRight, text_w))

        # Lat/lon and obs on subsequent line
        lat = station.get('lat', '—')
        lon = station.get('lng', '—')
        obs = station.get('observations', 0)
        line3 = f"Lat: {lat}, Lon: {lon}   Obs: {obs}"
        painter.drawText(tx, ty + 2*fm.height() + 12 + fm.ascent(), fm.elidedText(line3, Qt.ElideRight, text_w))

        painter.restore()

# ------------------- StationListView subclass for drop handling -------------------
class StationListView(QListView):
    def __init__(self, model: StationListModel, global_model_lookup, on_update_map=None, parent=None):
        super().__init__(parent)
        self.setModel(model)
        self.setSelectionMode(QListView.SingleSelection)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setDragDropMode(QListView.DragDrop)
        self.global_model_lookup = global_model_lookup  # callable to lookup station by id
        self.on_update_map = on_update_map
        self.setSpacing(4)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(MIME_STATION_ID):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(MIME_STATION_ID):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def add_selected(self, sid):
        pass

    def move_station(self, sid, src_model, dest_model, station):
        # Remove from source
        src_model.beginResetModel()
        src_model._all = [s for s in src_model._all if str(s.get('id')) != str(sid)]
        src_model.rebuild_filtered()
        src_model.endResetModel()

        # Add to destination
        dest_model.beginResetModel()
        dest_model._all.append(station)
        dest_model.rebuild_filtered()
        dest_model.endResetModel()

    def dropEvent(self, event):
        md = event.mimeData()
        if md.hasFormat(MIME_STATION_ID):
            sid = bytes(md.data(MIME_STATION_ID)).decode('utf-8')
            src_model, station = self.global_model_lookup(sid)
            if station is None:
                event.ignore()
                return

            dest_model: StationListModel = self.model()
            if src_model is dest_model:
                event.setDropAction(Qt.MoveAction)
                event.acceptProposedAction()
                return

            self.move_station(sid, src_model, dest_model, station)
            event.setDropAction(Qt.MoveAction)
            event.acceptProposedAction()

            # <-- CALL map refresh here
            if self.on_update_map:
                self.on_update_map()
        else:
            super().dropEvent(event)

# ------------------- Main Panel -------------------
class SatNOGSPanel(QWidget):
    """
    The main SatNOGSPanel class for showing two lists of SatNOGS stations, one for available stations and one
    of selected stations, allowing drag and drop between both lists.  Station pictures are lazy-loaded for
    added context.
    """
    def __init__(self, ground_config):
        super().__init__()
        self.setWindowTitle("SatNOGS Station Selector (Model/View)")
        self.resize(1100, 640)
        self.image_cache = ImageCache()
        self._load_stations()
        self.ground_config = ground_config

        preselected_names_or_ids = self.ground_config[GroundConfigType.STATIONS]
        preselected_set = set(str(x).lower() for x in (preselected_names_or_ids or []))

        # Split stations into selected and available
        selected_list = []
        available_list = []
        for s in self.all_stations:
            sid = str(s.get('id')).lower()
            sname = str(s.get('name', "")).lower()
            if sid in preselected_set or sname in preselected_set:
                selected_list.append(s)
            else:
                available_list.append(s)

        # Models
        self.selected_model = StationListModel(selected_list, image_cache=self.image_cache)
        self.available_model = StationListModel(available_list, image_cache=self.image_cache)
        self.selected_model._apply_filters = False
        self.selected_model._filtered = list(self.selected_model._all)

        # Views
        self.available_view = StationListView(self.available_model, self.global_lookup, on_update_map=self.refresh_map)
        self.selected_view = StationListView(self.selected_model, self.global_lookup, on_update_map=self.refresh_map)

        # Delegates
        delegate_a = StationDelegate(self.image_cache, parent=self.available_view)
        delegate_b = StationDelegate(self.image_cache, parent=self.selected_view)
        self.available_view.setItemDelegate(delegate_a)
        self.selected_view.setItemDelegate(delegate_b)

        # Filters & Pagination UI
        controls_layout = QHBoxLayout()
        # Band filter
        self.band_filter = QComboBox()
        self.band_filter.addItem("All")
        for b in sorted(self.all_bands):
            self.band_filter.addItem(b)
        self.band_filter.currentTextChanged.connect(self.on_filter_changed)
        controls_layout.addWidget(QLabel("Band:"))
        controls_layout.addWidget(self.band_filter)
        # Status filter
        self.status_filter = QComboBox()
        self.status_filter.addItem("All")
        for s in sorted(self.all_statuses):
            self.status_filter.addItem(s)
        self.status_filter.currentTextChanged.connect(self.on_filter_changed)
        controls_layout.addWidget(QLabel("Status:"))
        controls_layout.addWidget(self.status_filter)

        selected_ids = [str(s['id']) for s in selected_list]
        self.map_widget = StationMap(
            stations=self.all_stations,
            on_station_selected=self.on_station_clicked,
            selected_station_ids=selected_ids
        )

        # Pagination spin and nav
        self.page_spin = QSpinBox()
        self.page_spin.setMinimum(1)
        self.page_spin.setMaximum(self.available_model.total_pages())
        self.page_spin.setValue(1)
        self.page_spin.valueChanged.connect(self.on_page_changed)
        #controls_layout.addWidget(QLabel("Page:"))
        #controls_layout.addWidget(self.page_spin)

        self.prev_btn = QPushButton("◀")
        self.next_btn = QPushButton("▶")
        self.prev_btn.clicked.connect(self.go_prev)
        self.next_btn.clicked.connect(self.go_next)
        #controls_layout.addWidget(self.prev_btn)
        #controls_layout.addWidget(self.next_btn)

        # Left/Right layout for lists
        lists_layout = QHBoxLayout()
        left_vbox = QVBoxLayout()
        left_vbox.addWidget(QLabel("Available Stations:"))
        left_vbox.addWidget(self.available_view)

        # Pagination directly under available stations
        pagination_layout = QHBoxLayout()
        pagination_layout.addWidget(QLabel("Page:"))
        pagination_layout.addWidget(self.page_spin)
        pagination_layout.addWidget(self.prev_btn)
        pagination_layout.addWidget(self.next_btn)
        pagination_layout.addStretch()
        left_vbox.addLayout(pagination_layout)

        right_vbox = QVBoxLayout()
        right_vbox.addWidget(QLabel("Selected Stations:"))
        right_vbox.addWidget(self.selected_view)
        lists_layout.addLayout(left_vbox, 1)
        lists_layout.addLayout(right_vbox, 1)

        lists_panel = QWidget()
        lists_panel.setLayout(lists_layout)
        tabs = QTabWidget()
        tabs.addTab(lists_panel, "Station Lists")
        tabs.addTab(self.map_widget, "Station Map")

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(controls_layout)
        main_layout.addWidget(tabs)

        # set initial filter & page

        band_filter = "All"
        if self.ground_config[GroundConfigType.BAND_FILTER] in self.all_bands:
            self.band_filter.setCurrentText(self.ground_config[GroundConfigType.BAND_FILTER])
            band_filter = self.ground_config[GroundConfigType.BAND_FILTER]
        self.status_filter.setCurrentText("Online")

        print( "Setting band filter to ", band_filter)

        self.available_model.set_filter(band_filter, "Online")
        self._update_page_controls()
        self.refresh_map()

    def _load_stations(self) -> None:
        # Simple synchronous fetch for station list (could be threaded too)
        stations = fetch_json(API_URL)
        if not stations:
            QMessageBox.warning(self, "Fetch error", "Could not fetch station list from SatNOGS API.")
            stations = []
        # Ensure 'id' present as string for MIME
        for s in stations:
            if 'id' not in s:
                # fallback: generate id from name+lat/lon (rare)
                s['id'] = f"{s.get('name','x')}-{s.get('lat','')}-{s.get('lng','')}"
        self.all_stations = stations
        # compute bands & statuses
        bands = set()
        statuses = set()
        for s in self.all_stations:
            s['_bands'] = sorted({a.get('band') for a in s.get('antenna', []) if a.get('band')})
            for b in s['_bands']:
                bands.add(b)
            s['_status'] = s.get('status') or "Unknown"
            statuses.add(s['_status'])
        self.all_bands = bands
        self.all_statuses = statuses

    def on_station_clicked(self, sid, station) -> None:
        """
        Toggle the station between available and selected lists.
        """
        print("station clicked")
        # Determine which model currently has the station
        src_model, _ = self.global_lookup(sid)
        if src_model is None:
            return  # station not found

        # Determine destination model
        dest_model = self.selected_model if src_model is self.available_model else self.available_model

        # Move the station
        src_model.beginResetModel()
        src_model._all = [s for s in src_model._all if str(s.get('id')) != str(sid)]
        src_model.rebuild_filtered()  # rebuild filtered & reset page
        src_model.endResetModel()

        dest_model.beginResetModel()
        dest_model._all.append(station)
        dest_model.rebuild_filtered()
        dest_model.endResetModel()

        self.refresh_map()

    def global_lookup(self, station_id):
        """Return (model_that_contains_it, station_dict) or (None, None)"""
        # check available model
        for m in (self.available_model, self.selected_model):
            for s in m._all:
                if str(s.get('id')) == str(station_id):
                    return (m, s)
        return (None, None)

    # --- UI handlers ---
    def on_filter_changed(self, _=None) -> None:
        band = self.band_filter.currentText()
        status = self.status_filter.currentText()
        self.ground_config[GroundConfigType.BAND_FILTER] = band
        self.available_model.set_filter(band, status)
        self._update_page_controls()
        self.refresh_map()

    def _update_page_controls(self) -> None:
        total = self.available_model.total_pages()
        self.page_spin.blockSignals(True)
        self.page_spin.setMaximum(total)
        self.page_spin.setValue(self.available_model._page + 1)
        self.page_spin.blockSignals(False)
        # enable/disable nav
        self.prev_btn.setEnabled(self.available_model._page > 0)
        self.next_btn.setEnabled(self.available_model._page < total - 1)

    def on_page_changed(self, value: int) -> None:
        self.available_model.set_page(max(0, value - 1))
        self._update_page_controls()

    def go_prev(self) -> None:
        if self.available_model._page > 0:
            self.available_model.set_page(self.available_model._page - 1)
            self._update_page_controls()

    def go_next(self) -> None:
        if self.available_model._page < self.available_model.total_pages() - 1:
            self.available_model.set_page(self.available_model._page + 1)
            self._update_page_controls()

    def refresh_map(self) -> None:
        """
        Update the StationMap with current available + selected stations,
        respecting current filters.
        """
        # Filtered available stations (respecting current band/status filter)
        available_stations = self.available_model._filtered

        # Selected stations (always show these)
        selected_stations = self.selected_model._all

        # Combine: available stations + selected stations (avoiding duplicates)
        combined = {str(s['id']): s for s in available_stations}
        for s in selected_stations:
            combined[str(s['id'])] = s

        all_stations = list(combined.values())

        # Gather selected IDs
        selected_ids = {str(s['id']) for s in selected_stations}

        # Update the map
        self.map_widget.update_stations(
            stations=all_stations,
            selected_station_ids=selected_ids
        )

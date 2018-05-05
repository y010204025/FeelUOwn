import logging

from PyQt5.QtCore import Qt, QTime, pyqtSignal, pyqtSlot, QTimer
from PyQt5.QtGui import QFontMetrics, QPainter
from PyQt5.QtWidgets import (
    QAction,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from feeluown.widgets.components import LP_GroupHeader, LP_GroupItem

from feeluown import __upgrade_desc__
from feeluown.widgets.table_container import SongsTableContainer

from .consts import PlaybackMode
from .utils import parse_ms


logger = logging.getLogger(__name__)



class VolumeSlider(QSlider):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setOrientation(Qt.Horizontal)
        self.setMinimumWidth(100)
        self.setObjectName('player_volume_slider')
        self.setRange(0, 100)   # player volume range
        self.setValue(100)
        self.setToolTip('调教播放器音量')
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)


class ProgressLabel(QLabel):
    def __init__(self, text=None, parent=None):
        super().__init__(text, parent)
        self.duration_text = '00:00'

    def set_duration(self, ms):
        m, s = parse_ms(ms)
        duration = QTime(0, m, s)
        self.duration_text = duration.toString('mm:ss')

    def update_state(self, ms):
        m, s = parse_ms(ms)
        position = QTime(0, m, s)
        position_text = position.toString('mm:ss')
        self.setText(position_text + '/' + self.duration_text)


class ProgressSlider(QSlider):
    def __init__(self, app, parent=None):
        super().__init__(parent)

        self.setOrientation(Qt.Horizontal)
        self.setMinimumWidth(400)
        self.setObjectName('player_progress_slider')

        self.sliderMoved.connect(self.seek)

    def set_duration(self, ms):
        self.setRange(0, ms / 1000)

    def update_state(self, ms):
        self.setValue(ms / 1000)

    def seek(self, second):
        self._app.player.setPosition(second)


class PlayerControlPanel(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self._layout = QHBoxLayout(self)
        self.previous_btn = QPushButton('上一首', self)
        self.pp_btn = QPushButton('播放', self)
        self.next_btn = QPushButton('下一首', self)

        self._sub_layout = QGridLayout()
        self.song_title_label = SongLabel(parent=self)
        self.progress_slider = ProgressSlider(self)

        self.pms_btn = PlaybackModeSwitchBtn(self._app, self)

        self.volume_slider = VolumeSlider(self)
        self.progress_label = ProgressLabel('00:00/00:00', self)

        self._btn_container = QFrame(self)
        self._slider_container = QFrame(self)

        self._bc_layout = QHBoxLayout(self._btn_container)
        self._sc_layout = QHBoxLayout(self._slider_container)

        self.setup_ui()

        self.next_btn.clicked.connect(self._app.player.playlist.play_next)
        self.previous_btn.clicked.connect(self._app.player.playlist.play_previous)
        self.pp_btn.clicked.connect(self._app.player.toggle)

    def setup_ui(self):
        self._btn_container.setFixedWidth(140)
        self._slider_container.setMinimumWidth(700)
        self.progress_slider.setMinimumWidth(550)
        self.progress_label.setFixedWidth(90)

        self._bc_layout.addWidget(self.previous_btn)
        self._bc_layout.addStretch(1)
        self._bc_layout.addWidget(self.pp_btn)
        self._bc_layout.addStretch(1)
        self._bc_layout.addWidget(self.next_btn)

        self._sc_layout.addLayout(self._sub_layout)
        self._sc_layout.addSpacing(10)
        self._sc_layout.addWidget(self.progress_label)
        self._sc_layout.addSpacing(5)
        self._sc_layout.addWidget(self.volume_slider)
        self._sc_layout.setSpacing(0)
        self._sc_layout.setContentsMargins(0, 0, 0, 0)

        self._sub_layout.setSpacing(0)
        self._sub_layout.setContentsMargins(0, 0, 0, 0)
        self._sub_layout.addWidget(self.song_title_label, 0, 0, 1, -1)
        self._sub_layout.setRowStretch(0, 1)
        self._sub_layout.addWidget(self.pms_btn, 0, 1, Qt.AlignRight)
        self._sub_layout.addWidget(self.progress_slider, 1, 0, 2, -1, Qt.AlignLeft)

        self._layout.addWidget(self._btn_container)
        self._layout.addSpacing(10)
        self._layout.addWidget(self._slider_container)
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)


class TopPanel(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self._layout = QHBoxLayout(self)
        self.pc_panel = PlayerControlPanel(self._app, self)

        self.setObjectName('top_panel')
        self.set_theme_style()
        self.setup_ui()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
                color: {1};
                border-top: 3px inset {3};
            }}
        '''.format(self.objectName(),
                   theme.foreground.name(),
                   theme.color0_light.name(),
                   theme.color0_light.name())
        self.setStyleSheet(style_str)

    def setup_ui(self):
        self.setFixedHeight(60)
        self._layout.addSpacing(5)
        self._layout.addWidget(self.pc_panel)
        self._layout.addSpacing(10)


class LP_LibraryPanel(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.header = LP_GroupHeader(self._app, '我的音乐')
        self.current_playlist_item = LP_GroupItem(self._app, '当前播放列表')
        self.current_playlist_item.set_img_text('❂')
        self._layout = QVBoxLayout(self)

        self.setObjectName('lp_library_panel')
        self.set_theme_style()
        self.setup_ui()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
            }}
        '''.format(self.objectName(),
                   theme.color3.name())
        self.setStyleSheet(style_str)

    def setup_ui(self):
        self._layout.addSpacing(3)
        self._layout.addWidget(self.header)
        self._layout.addWidget(self.current_playlist_item)

    def add_item(self, item):
        self._layout.addWidget(item)


class LP_PlaylistsPanel(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.header = LP_GroupHeader(self._app, '歌单')
        self._layout = QVBoxLayout(self)
        self.setObjectName('lp_playlists_panel')

        self.set_theme_style()
        self.setup_ui()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
            }}
        '''.format(self.objectName(),
                   theme.color5.name())
        self.setStyleSheet(style_str)

    def add_item(self, item):
        self._layout.addWidget(item)

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        self._layout.addWidget(self.header)


class LeftPanel(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.library_panel = LP_LibraryPanel(self._app)
        self.playlists_panel = LP_PlaylistsPanel(self._app)

        self._layout = QVBoxLayout(self)
        self.setLayout(self._layout)
        self.setObjectName('c_left_panel')
        self.set_theme_style()
        self.setup_ui()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
            }}
        '''.format(self.objectName(),
                   theme.color5.name())
        self.setStyleSheet(style_str)

    def setup_ui(self):
        self._layout.addWidget(self.library_panel)
        self._layout.addWidget(self.playlists_panel)
        self._layout.addStretch(1)


class LeftPanel_Container(QScrollArea):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.left_panel = LeftPanel(self._app)
        self._layout = QVBoxLayout(self)  # no layout, no children
        self.setWidget(self.left_panel)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)

        self.setObjectName('c_left_panel_container')
        self.set_theme_style()
        self.setMinimumWidth(180)
        self.setMaximumWidth(220)

        self.setup_ui()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
                border: 0px;
                border-right: 3px inset {1};
            }}
        '''.format(self.objectName(),
                   theme.color0_light.name())
        self.setStyleSheet(style_str)

    def setup_ui(self):
        pass


class RightPanel(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.widget = None

        self._layout = QHBoxLayout(self)
        self.setLayout(self._layout)
        self.setObjectName('right_panel')
        self.set_theme_style()

    def set_theme_style(self):
        style_str = '''
            #{0} {{
                background: transparent;
                padding: 20px 30px 0px 30px;
            }}
        '''.format(self.objectName())
        self.setStyleSheet(style_str)

    def set_widget(self, widget):
        if self.widget and self.widget != widget:
            self._layout.removeWidget(self.widget)
            self.widget.hide()
            widget.show()
            self._layout.addWidget(widget)
        else:
            self._layout.addWidget(widget)
        self.widget = widget


class RightPanel_Container(QScrollArea):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.right_panel = RightPanel(self._app)
        self._layout = QVBoxLayout(self)
        self.setWidget(self.right_panel)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)

        self.setObjectName('c_left_panel')
        self.set_theme_style()
        self.setup_ui()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: transparent;
                border: 0px;
            }}
        '''.format(self.objectName(),
                   theme.color5.name())
        self.setStyleSheet(style_str)

    def setup_ui(self):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)


class CentralPanel(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.left_panel_container = LeftPanel_Container(self._app, self)
        self.right_panel_container = RightPanel_Container(self._app, self)
        self.left_panel = self.left_panel_container.left_panel
        self.right_panel = self.right_panel_container.right_panel

        self._layout = QHBoxLayout(self)
        self.set_theme_style()
        self.setup_ui()

    def set_theme_style(self):
        style_str = '''
            #{0} {{
                background: transparent;
            }}
        '''.format(self.objectName())
        self.setStyleSheet(style_str)

    def setup_ui(self):
        self._layout.addWidget(self.left_panel_container)
        self._layout.addWidget(self.right_panel_container)


class SongLabel(QLabel):
    def __init__(self, text=None, parent=None):
        super().__init__(text, parent)
        self.set_song('No song is playing')

    def set_song(self, song_text):
        self.setText('♪  ' + song_text + ' ')


class PlaybackModeSwitchBtn(QPushButton):
    def __init__(self, app, parent=None):
        super().__init__(parent=parent)
        self._app = app

        self.setObjectName('player_mode_switch_btn')
        self.set_theme_style()
        self.set_text('循环')

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: {1};
                color: {2};
                border: 0px;
                padding: 0px 4px;
            }}
        '''.format(self.objectName(),
                   theme.color6.name(),
                   theme.background.name())
        self.setStyleSheet(style_str)

    def set_text(self, text):
        self.setText('♭ ' + text)

    def on_playback_mode_changed(self, playback_mode):
        self.set_text(playback_mode.value)


class ThemeCombo(QComboBox):
    clicked = pyqtSignal()
    signal_change_theme = pyqtSignal([str])

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.setObjectName('theme_switch_btn')
        self.setEditable(False)
        self.maximum_width = 150
        self.set_theme_style()
        self.setFrame(False)
        self.current_theme = self._app.theme_manager.current_theme.name
        self.themes = [self.current_theme]
        self.set_themes(self.themes)

        self.currentIndexChanged.connect(self.on_index_changed)

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: {1};
                color: {2};
                border: 0px;
                padding: 0px 4px;
                border-radius: 0px;
            }}
            #{0}::drop-down {{
                width: 0px;
                border: 0px;
            }}
            #{0} QAbstractItemView {{
                border: 0px;
                min-width: 200px;
            }}
        '''.format(self.objectName(),
                   theme.color4.name(),
                   theme.background.name(),
                   theme.foreground.name())
        self.setStyleSheet(style_str)

    @pyqtSlot(int)
    def on_index_changed(self, index):
        if index < 0 or not self.themes:
            return
        metrics = QFontMetrics(self.font())
        if self.themes[index] == self.current_theme:
            return
        self.current_theme = self.themes[index]
        name = '❀ ' + self.themes[index]
        width = metrics.width(name)
        if width < self.maximum_width:
            self.setFixedWidth(width + 10)
            self.setItemText(index, name)
            self.setToolTip(name)
        else:
            self.setFixedWidth(self.maximum_width)
            text = metrics.elidedText(name, Qt.ElideRight,
                                      self.width())
            self.setItemText(index, text)
            self.setToolTip(text)
        self.signal_change_theme.emit(self.current_theme)

    def add_item(self, text):
        self.addItem('❀ ' + text)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and \
                self.rect().contains(event.pos()):
            self.clicked.emit()
            self.showPopup()

    def set_themes(self, themes):
        self.clear()
        if self.current_theme:
            self.themes = [self.current_theme]
            self.add_item(self.current_theme)
        else:
            self.themes = []
        for theme in themes:
            if theme not in self.themes:
                self.add_item(theme)
                self.themes.append(theme)


class PlayerStateLabel(QLabel):
    def __init__(self, app, text=None, parent=None):
        super().__init__('♫', parent)
        self._app = app

        self.setObjectName('player_state_label')
        self.setToolTip('这里显示的是播放器的状态\n'
                        'Buffered 代表该音乐已经可以开始播放\n'
                        'Stalled 表示正在加载或者由于某种原因而被迫中断\n'
                        'Loading 代表正在加载该音乐\n'
                        'Loaded 代表改歌曲是本地歌曲，并加载完毕\n'
                        'Failed 代表加载音乐失败\n'
                        '这里的进度条代表加载音乐的进度')
        self.set_theme_style()
        self._progress = 100
        self._show_progress = False

    def paintEvent(self, event):
        if self._show_progress:
            painter = QPainter(self)
            p_bg_color = self._app.theme_manager.current_theme.color0
            painter.fillRect(self.rect(), p_bg_color)
            bg_color = self._app.theme_manager.current_theme.color6_light
            rect = self.rect()
            percent = self._progress * 1.0 / 100
            rect.setWidth(int(rect.width() * percent))
            painter.fillRect(rect, bg_color)
            painter.drawText(self.rect(), Qt.AlignVCenter | Qt.AlignHCenter,
                             'buffering' + str(self._progress) + '%')
            self._show_progress = False
        else:
            super().paintEvent(event)

    def show_progress(self, progress):
        self._progress = progress
        self._show_progress = True
        if self._progress == 100:
            self._show_progress = False
        self.update()

    def set_text(self, text):
        self.setText(('♫ ' + text).upper())

    @property
    def common_style(self):
        style_str = '''
            #{0} {{
                padding-left: 3px;
                padding-right: 5px;
            }}
        '''.format(self.objectName())
        return style_str

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: {1};
                color: {2};
            }}
        '''.format(self.objectName(),
                   theme.color6_light.name(),
                   theme.color7.name())
        self.setStyleSheet(style_str + self.common_style)

    def set_error_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: {1};
                color: {2};
            }}
        '''.format(self.objectName(),
                   theme.color1_light.name(),
                   theme.color7.name())
        self.setStyleSheet(style_str + self.common_style)

    def set_normal_style(self):
        self.set_theme_style()


class MessageLabel(QLabel):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self.setObjectName('message_label')
        self._interval = 3
        self.timer = QTimer()
        self.queue = []
        self.hide()

        self.timer.timeout.connect(self.access_message_queue)

    @property
    def common_style(self):
        style_str = '''
            #{0} {{
                padding-left: 3px;
                padding-right: 5px;
            }}
        '''.format(self.objectName())
        return style_str

    def _set_error_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: {1};
                color: {2};
            }}
        '''.format(self.objectName(),
                   theme.color1_light.name(),
                   theme.color7_light.name())
        self.setStyleSheet(style_str + self.common_style)

    def _set_normal_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: {1};
                color: {2};
            }}
        '''.format(self.objectName(),
                   theme.color6_light.name(),
                   theme.color7.name())
        self.setStyleSheet(style_str + self.common_style)

    def show_message(self, text, error=False):
        if self.isVisible():
            self.queue.append({'error': error, 'message': text})
            self._interval = 1.5
            return
        if error:
            self._set_error_style()
        else:
            self._set_normal_style()
        self.setText(str(len(self.queue)) + ': ' + text)
        self.show()
        self.timer.start(self._interval * 1000)

    def access_message_queue(self):
        self.hide()
        if self.queue:
            m = self.queue.pop(0)
            self.show_message(m['message'], m['error'])
        else:
            self._interval = 3


class AppStatusLabel(QLabel):
    clicked = pyqtSignal()

    def __init__(self, app, text=None, parent=None):
        super().__init__(text, parent)
        self._app = app

        self.setText('♨ Normal'.upper())
        self.setToolTip('点击可以切换到其他模式哦 ~\n'
                        '不过暂时还没实现这个功能...敬请期待 ~\n' +
                        '此版本更新摘要:\n' +
                        __upgrade_desc__)
        self.setObjectName('app_status_label')
        self.set_theme_style()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: {1};
                color: {3};
                padding-left: 5px;
                padding-right: 5px;
                font-size: 14px;
            }}
            #{0}:hover {{
                color: {2};
            }}
        '''.format(self.objectName(),
                   theme.color4.name(),
                   theme.color2.name(),
                   theme.background.name())
        self.setStyleSheet(style_str)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and \
                self.rect().contains(event.pos()):
            self.clicked.emit()


class NetworkStatus(QLabel):
    def __init__(self, app, text=None, parent=None):
        super().__init__(text, parent)
        self._app = app

        self.setToolTip('这里显示的是当前网络状态')
        self.setObjectName('network_status_label')
        self.set_theme_style()
        self._progress = 100
        self._show_progress = False

        self.set_state(1)

    def paintEvent(self, event):
        if self._show_progress:
            painter = QPainter(self)
            p_bg_color = self._app.theme_manager.current_theme.color0
            painter.fillRect(self.rect(), p_bg_color)
            bg_color = self._app.theme_manager.current_theme.color3
            rect = self.rect()
            percent = self._progress * 1.0 / 100
            rect.setWidth(int(rect.width() * percent))
            painter.fillRect(rect, bg_color)
            painter.drawText(self.rect(), Qt.AlignVCenter | Qt.AlignHCenter,
                             str(self._progress) + '%')
            self._show_progress = False
        else:
            super().paintEvent(event)

    @property
    def common_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: {1};
                color: {2};
                padding-left: 5px;
                padding-right: 5px;
                font-size: 14px;
                font-weight: bold;
            }}
        '''.format(self.objectName(),
                   theme.color3.name(),
                   theme.background.name())
        return style_str

    def set_theme_style(self):
        self.setStyleSheet(self.common_style)

    def _set_error_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: {1};
            }}
        '''.format(self.objectName(),
                   theme.color5.name())
        self.setStyleSheet(self.common_style + style_str)

    def _set_normal_style(self):
        self.setStyleSheet(self.common_style)

    def set_state(self, state):
        if state == 0:
            self._set_error_style()
            self.setText('✕')
        elif state == 1:
            self._set_normal_style()
            self.setText('✓')

    def show_progress(self, progress):
        self._progress = progress
        self._show_progress = True
        if self._progress == 100:
            self._show_progress = False
        self.update()


class StatusPanel(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app

        self._layout = QHBoxLayout(self)
        self.player_state_label = PlayerStateLabel(self._app)
        self.app_status_label = AppStatusLabel(self._app)
        self.network_status_label = NetworkStatus(self._app)
        self.message_label = MessageLabel(self._app)
        self.theme_switch_btn = ThemeCombo(self._app, self)

        self.setup_ui()
        self.setObjectName('status_panel')
        self.set_theme_style()

    def set_theme_style(self):
        theme = self._app.theme_manager.current_theme
        style_str = '''
            #{0} {{
                background: {1};
            }}
        '''.format(self.objectName(),
                   theme.color0.name())
        self.setStyleSheet(style_str)

    def setup_ui(self):
        self.setFixedHeight(18)
        self._layout.addWidget(self.player_state_label)
        self._layout.addWidget(self.app_status_label)
        self._layout.addWidget(self.network_status_label)
        self._layout.addStretch(0)
        self._layout.addWidget(self.message_label)
        self._layout.addStretch(0)
        self._layout.addWidget(self.theme_switch_btn)
        self._layout.setSpacing(0)
        self._layout.setContentsMargins(0, 0, 0, 0)


class LyricFrame(QFrame):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app


class Ui(object):
    def __init__(self, app):
        self._app = app
        self._layout = QVBoxLayout(app)
        self.top_panel = TopPanel(app, app)
        self.central_panel = CentralPanel(app, app)
        self.status_panel = StatusPanel(app, app)
        self.status_panel.hide()
        self.setup()

    def setup(self):
        self._layout.addWidget(self.central_panel)
        self._layout.addWidget(self.top_panel)
        self._layout.addWidget(self.status_panel)

    def show_playlist(self, playlist):
        if not hasattr(self, 'songs_table_container'):
            self.songs_table_container = SongsTableContainer(self._app, self._app)
        self.songs_table_container.show_playlist(playlist)
        self.central_panel.right_panel.set_widget(self.songs_table_container)

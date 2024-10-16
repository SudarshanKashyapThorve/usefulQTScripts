import sys
import os
import random
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (
    QApplication, QPushButton, QLabel, QVBoxLayout, QWidget,
    QHBoxLayout
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import (
    QIcon, QPixmap, QPainter, QColor, QFontMetrics
)
from PyQt5.QtSvg import QSvgRenderer

# Define minimum window size for showing notifications
MIN_WIDTH = 400
MIN_HEIGHT = 300

# Define notification types
class NotificationType:
    SUCCESS = 'SUCCESS'
    INFO = 'INFO'
    ERROR = 'ERROR'
    WARNING = 'WARNING'
    MORE = 'MORE'  # New notification type for "more notifications"

class Notifier(QWidget):
    def __init__(self, parent, message, notification_type=NotificationType.INFO, auto_hide=True, close_callback=None):
        # Use QApplication's active window if parent is None
        if parent is None:
            parent = QApplication.activeWindow()
        super().__init__(parent)

        self.auto_hide = auto_hide
        self.close_callback = close_callback
        self.original_message = message
        self.notification_type = notification_type
        self.parent = parent  # Store reference to parent
        self.is_more_notifications = False  # Flag to identify "more notifications" message

        self.maxWidth = 300

        self.setStyleSheet("""
            QWidget#notification {
                font-size: 14px;
            }
        """)
        self.setObjectName("notification")

        # Enable window drop shadow and translucent background
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Create close button with SVG icon using QPushButton
        self.close_button = QPushButton(self)
        self.close_button.setFixedSize(16, 16)
        self.close_button.setCursor(Qt.PointingHandCursor)
        self.close_button.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
            }
        """)
        # Load the SVG icon and create normal and hover pixmaps
        self.close_icon = self.create_colored_icon('cross_icon.svg', '#ffffff', size=16)
        self.close_icon_hover = self.create_colored_icon('cross_icon.svg', '#ff0000', size=16)
        if not self.close_icon or self.close_icon.isNull():
            print("Close icon is null or not loaded properly!")
            self.close_button.setText('✕')  # Use Unicode character as fallback
        else:
            self.close_button.setIcon(self.close_icon)
            self.close_button.setIconSize(self.close_button.size())
        self.close_button.clicked.connect(self.close_notification)
        self.close_button.installEventFilter(self)

        # Add icon label to display the notification type icon
        self.icon_label = QLabel(self)
        self.icon_label.setFixedSize(20, 20)  # Reduced size from 24 to 20
        self.icon_label.setAlignment(Qt.AlignCenter)

        # Add label to display the message
        self.label = QLabel(self)
        self.label.setWordWrap(False)
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

        # Set tooltip on the label to display the full message
        self.label.setToolTip(self.original_message)

        # Layout for the icon, label, and close button
        layout = QHBoxLayout()
        layout.addWidget(self.icon_label)
        layout.addWidget(self.label)
        layout.addWidget(self.close_button)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)
        self.setLayout(layout)

        # Initialize timer but do not start it yet
        self.timer = None
        self.timer_started = False  # Flag to track if the timer has been started

        # Set the message and style
        self.set_message(message, notification_type)
        self.apply_notification_style()

    def apply_notification_style(self):
        """Apply styles based on the notification type."""
        # Define colors for each notification type (text color only)
        colors = {
            NotificationType.SUCCESS: '#C5E384',  # Metallic Green
            NotificationType.INFO: '#8ED2F9',     # Metallic Blue
            NotificationType.ERROR: '#FF474C',    # Metallic Red
            NotificationType.WARNING: '#FDD017',  # Metallic Yellow/Gold
            NotificationType.MORE: '#D1D8DD'      # Metallic Silver
        }

        icons = {
            NotificationType.SUCCESS: 'success.svg',
            NotificationType.INFO: 'info.svg',
            NotificationType.ERROR: 'error.svg',
            NotificationType.WARNING: 'warn.svg',
            NotificationType.MORE: 'notification.svg'
        }

        color = colors.get(self.notification_type, colors[NotificationType.INFO])
        icon_path = icons.get(self.notification_type, 'info.svg')

        # Set text color
        self.label.setStyleSheet(f"color: {color};")

        # Update the close button icon color
        self.close_icon = self.create_colored_icon('cross_icon.svg', color, size=16)
        self.close_icon_hover = self.create_colored_icon('cross_icon.svg', '#ff0000', size=16)
        if not self.close_icon or self.close_icon.isNull():
            self.close_button.setText('✕')
        else:
            self.close_button.setIcon(self.close_icon)
            self.close_button.setIconSize(self.close_button.size())

        # Set the icon label pixmap
        icon = self.create_colored_icon(icon_path, color, size=20)  # Reduced size from 24 to 20
        if not icon or icon.isNull():
            # Use a placeholder or Unicode character if icon not found
            self.icon_label.setText('❓')
        else:
            self.icon_label.setPixmap(icon.pixmap(20, 20))  # Adjusted size

    def paintEvent(self, event):
        """Draw the background with rounded corners."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()

        # Draw background
        painter.setBrush(QColor('#333333'))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 8, 8)

        # Note: Colored border removed as per request

    def create_colored_icon(self, svg_path, color, size):
        """Create a QIcon from an SVG file with the specified color and size."""
        if not os.path.exists(svg_path):
            print(f"SVG file not found: {svg_path}")
            return QIcon()
        renderer = QSvgRenderer(svg_path)
        if not renderer.isValid():
            print(f"Invalid SVG file: {svg_path}")
            return QIcon()
        img_size = QtCore.QSize(size, size)
        image = QPixmap(img_size)
        image.fill(Qt.transparent)

        painter = QPainter(image)
        renderer.render(painter)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(image.rect(), QColor(color))
        painter.end()

        return QIcon(image)

    def eventFilter(self, obj, event):
        if obj == self.close_button:
            if event.type() == QtCore.QEvent.Enter:
                self.close_button.setIcon(self.close_icon_hover)
            elif event.type() == QtCore.QEvent.Leave:
                self.close_button.setIcon(self.close_icon)
        return super().eventFilter(obj, event)

    def set_message(self, message, notification_type=None):
        """Set the notification message with text elision and adjust its size."""
        self.label.setText(message)
        self.label.setToolTip(self.original_message)
        if notification_type:
            self.notification_type = notification_type
            self.apply_notification_style()
        self.adjust_size()

        # Set flag if this is the "more notifications" message
        self.is_more_notifications = self.notification_type == NotificationType.MORE

    def adjust_size(self):
        """Adjust the size of the notification frame based on content."""
        # Adjust maxWidth based on parent width to prevent overflow
        parent_width = self.parent.width() if self.parent else self.maxWidth
        self.maxWidth = min(300, parent_width - 40)

        self.setFixedWidth(self.maxWidth)
        label_max_width = self.maxWidth - self.close_button.width() - self.icon_label.width() - 50  # Adjusted for icon

        self.label.setMaximumWidth(label_max_width)

        # Use QFontMetrics to elide text as needed
        font_metrics = QFontMetrics(self.label.font())
        elided_text = font_metrics.elidedText(self.label.text(), Qt.ElideRight, label_max_width)
        self.label.setText(elided_text)

        self.label.adjustSize()
        self.setFixedHeight(max(self.label.height(), self.icon_label.height(), self.close_button.height()) + 20)

    def show_notification(self):
        """Show the notification."""
        self.adjust_size()
        self.show()

        # Start the auto-hide timer when the notification is shown for the first time
        if self.auto_hide and not self.timer_started:
            if self.timer is None:
                self.timer = QTimer(self)
                self.timer.setSingleShot(True)
                self.timer.timeout.connect(self.close_notification)
            self.timer.start(5000)
            self.timer_started = True

    def hide_notification(self):
        """Hide the notification without deleting it."""
        self.hide()
        # Do not stop the timer; it should continue running

    def close_notification(self):
        """Close the notification."""
        self.hide()
        if self.close_callback:
            self.close_callback(self)
        self.deleteLater()

class NotificationIcon(QWidget):
    """Widget to display a notification icon with the number of notifications."""
    def __init__(self, parent, notification_manager):
        # Use QApplication's active window if parent is None
        if parent is None:
            parent = QApplication.activeWindow()
        super().__init__(parent)
        self.parent = parent
        self.notification_manager = notification_manager

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

        # Layout
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)
        self.setLayout(layout)

        # Notification icon
        self.icon_label = QLabel(self)
        self.icon_label.setFixedSize(20, 20)  # Reduced size from 24 to 20
        icon = self.create_colored_icon('notification.svg', '#FFFFFF', size=20)
        if icon and not icon.isNull():
            self.icon_label.setPixmap(icon.pixmap(20, 20))
        else:
            self.icon_label.setText('🔔')  # Use Unicode bell as fallback
        self.icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_label)

        # Count label
        self.count_label = QLabel(self)
        self.count_label.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 14px;")
        self.count_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.count_label)

        # Adjust size and position
        self.adjust_size()
        self.adjust_position()

    def create_colored_icon(self, svg_path, color, size):
        """Create a QIcon from an SVG file with the specified color and size."""
        if not os.path.exists(svg_path):
            print(f"SVG file not found: {svg_path}")
            return QIcon()
        renderer = QSvgRenderer(svg_path)
        if not renderer.isValid():
            print(f"Invalid SVG file: {svg_path}")
            return QIcon()
        img_size = QtCore.QSize(size, size)
        image = QPixmap(img_size)
        image.fill(Qt.transparent)

        painter = QPainter(image)
        renderer.render(painter)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(image.rect(), QColor(color))
        painter.end()

        return QIcon(image)

    def update_count(self):
        """Update the notification count displayed."""
        total_notifications = len(self.notification_manager.active_notifications) + len(self.notification_manager.notification_queue)
        self.count_label.setText(str(total_notifications))
        self.adjust_size()
        self.adjust_position()

    def adjust_size(self):
        """Adjust the size of the icon widget based on content."""
        # Calculate the width based on the contents
        self.count_label.adjustSize()
        content_width = self.icon_label.width() + self.count_label.width() + 30  # 30 for margins and spacing
        self.setFixedSize(content_width, 44)  # Height is 44 to match Notifier's height

    def adjust_position(self):
        """Adjust the position of the icon."""
        if not self.parent:
            return
        main_window_pos = self.parent.mapToGlobal(QtCore.QPoint(0, 0))
        x = main_window_pos.x()
        y = main_window_pos.y()
        width = self.parent.width()

        x_offset = x + width - self.width() - 20  # 20 px margin
        y_offset = y + 20  # 20 px from top

        self.move(x_offset, y_offset)

    def paintEvent(self, event):
        """Draw the background with rounded corners."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()

        # Draw background
        painter.setBrush(QColor('#333333'))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, 8, 8)

        # Note: Colored border removed as per request

class NotificationManager(QtCore.QObject):
    _instance = None  # Class variable to hold the singleton instance

    def __init__(self, parent=None, max_notifications=3, auto_hide=True):
        super().__init__(parent)
        # Use QApplication's active window if parent is None
        if parent is None:
            parent = QApplication.activeWindow()
        self.parent = parent
        self.max_notifications = max_notifications
        self.auto_hide = auto_hide
        self.active_notifications = []
        self.notification_queue = []

        # Create the notification icon widget
        self.notification_icon = NotificationIcon(self.parent, self)
        self.notification_icon.hide()

        # Track the main window's state
        if self.parent is not None:
            self.parent.installEventFilter(self)

    @classmethod
    def get_instance(cls, parent=None):
        if cls._instance is None:
            cls._instance = cls(parent)
        elif parent is not None and cls._instance.parent is None:
            # Update the parent if it was previously None
            cls._instance.parent = parent
            cls._instance.notification_icon.setParent(parent)
            cls._instance.notification_icon.parent = parent
            cls._instance.notification_icon.adjust_position()
            if cls._instance.parent is not None:
                cls._instance.parent.installEventFilter(cls._instance)
        return cls._instance

    @classmethod
    def show_notification(cls, message, notification_type=NotificationType.INFO, auto_hide=True, parent=None):
        """Class method to show a notification using the singleton instance."""
        instance = cls.get_instance(parent)
        instance.add_notification(message, notification_type, auto_hide)

    def eventFilter(self, obj, event):
        if obj == self.parent:
            if event.type() == QtCore.QEvent.WindowStateChange:
                self._position_notifications()
            elif event.type() == QtCore.QEvent.ActivationChange:
                self._position_notifications()
            elif event.type() == QtCore.QEvent.Resize:
                self._position_notifications()
        return False

    def add_notification(self, message, notification_type=NotificationType.INFO, auto_hide=True):
        """Add a new notification and handle the queue."""
        if len(self.active_notifications) < self.max_notifications:
            self._show_notification(message, notification_type, auto_hide)
        else:
            self.notification_queue.append((message, notification_type, auto_hide))
            self._update_top_notification()
        self.notification_icon.update_count()

    def _show_notification(self, message, notification_type, auto_hide):
        """Show a new notification."""
        notification = Notifier(
            self.parent,
            message,
            notification_type=notification_type,
            auto_hide=auto_hide,
            close_callback=self._remove_notification
        )
        self.active_notifications.append(notification)
        self._position_notifications()
        notification.show_notification()

    def _remove_notification(self, notification):
        """Remove a notification from the active list and process the queue."""
        # Check if the notification is the "more notifications" notification
        if notification.is_more_notifications:
            # Close all notifications and clear the queue
            for n in self.active_notifications:
                n.hide()
                n.deleteLater()
            self.active_notifications.clear()
            self.notification_queue.clear()
            self.notification_icon.update_count()
        else:
            if notification in self.active_notifications:
                self.active_notifications.remove(notification)
            self._process_next_notification()
            self._position_notifications()
            self.notification_icon.update_count()

    def _process_next_notification(self):
        """Show the next notification from the queue."""
        if self.notification_queue:
            next_message, next_type, next_auto_hide = self.notification_queue.pop(0)
            self.add_notification(next_message, next_type, next_auto_hide)
        self._update_top_notification()

    def _update_top_notification(self):
        """Update the topmost notification to show remaining queued notifications."""
        if len(self.active_notifications) == self.max_notifications:
            remaining = len(self.notification_queue)
            top_notification = self.active_notifications[0]
            if remaining > 0:
                top_notification.set_message(
                    f"You have {remaining} more notifications.",
                    notification_type=NotificationType.MORE
                )
            else:
                top_notification.set_message(
                    top_notification.original_message,
                    notification_type=top_notification.notification_type
                )
        else:
            for notification in self.active_notifications:
                notification.set_message(
                    notification.original_message,
                    notification_type=notification.notification_type
                )

    def _position_notifications(self):
        """Reposition all active notifications or show the notification icon based on window size."""
        if not self.parent:
            return

        # Check if window is larger than minimum size
        if self.parent.width() >= MIN_WIDTH and self.parent.height() >= MIN_HEIGHT:
            # Show notifications
            self.notification_icon.hide()
            # Get the global position of the parent window
            main_window_pos = self.parent.mapToGlobal(QtCore.QPoint(0, 0))
            x = main_window_pos.x()
            y = main_window_pos.y()
            width = self.parent.width()

            top_margin = 20  # Top margin for the first notification
            spacing = 5  # Space between notifications

            # Position each notification
            for i, notification in enumerate(self.active_notifications):
                notification.adjust_size()
                y_offset = y + top_margin + i * (notification.height() + spacing)
                x_offset = x + width - notification.width() - 20

                notification.move(x_offset, y_offset)
                notification.show()  # Use show() instead of show_notification()
        else:
            # Hide notifications and show icon with count
            for notification in self.active_notifications:
                notification.hide_notification()
            self.notification_icon.update_count()
            self.notification_icon.adjust_position()
            self.notification_icon.show()

# Example usage
if __name__ == '__main__':
    def main():
        app = QApplication(sys.argv)

        # Set the tooltip stylesheet globally
        app.setStyleSheet("""
            QToolTip {
                background-color: #333333;
                color: white;
                border: none;
                padding: 5px;
                border-radius: 5px;
            }
        """)

        window = QWidget()
        window.setWindowTitle("Main Application Window")
        window.resize(600, 400)  # Start with a size larger than MIN_WIDTH and MIN_HEIGHT
        layout = QVBoxLayout(window)
        button = QPushButton("Show Notification", window)
        layout.addWidget(button)
        window.setLayout(layout)

        # Connect the button to show a notification
        def on_button_clicked():
            sample_texts = [
                "Operation completed successfully.",
                "Information: The process is ongoing.",
                "Error: Unable to connect to the server.",
                "Warning: Low disk space detected.",
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vestibulum vehicula ex eu urna volutpat."
            ]
            notification_types = [
                NotificationType.SUCCESS,
                NotificationType.INFO,
                NotificationType.ERROR,
                NotificationType.WARNING
            ]
            message = random.choice(sample_texts)
            notification_type = random.choice(notification_types)
            NotificationManager.show_notification(message, notification_type, auto_hide=True)

        button.clicked.connect(on_button_clicked)

        window.show()
        sys.exit(app.exec_())

    main()

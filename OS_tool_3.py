import sys
import os
import csv
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton, QFileDialog,
                             QHBoxLayout, QVBoxLayout, QWidget, QMessageBox)
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QPoint, QSize
from PyQt5.QtWidgets import QScrollArea, QLineEdit
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtGui import QIcon


# from PIL import Image


class ImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.points = []
        self.scale_factor = 1.0
        self.image = None
        self.index = 0
        self.setMouseTracking(True)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.checkMode = False
        self.checking = 0
        
        # For panning
        self.pan_enabled = False
        self.last_pan_pos = QPoint(0, 0)
        self.offset_x = 0
        self.offset_y = 0
        
        # Sync with other label
        self.paired_label = None
        self.paired_scroll_area = None
        
        # 用于添加标注点
        self.mainWindow = None

    def set_image(self, image):
        self.image = image
        self.update_display()

    def update_display(self):
        if self.image:
            scaled_image = self.image.scaled(
                int(self.image.width() * self.scale_factor),
                int(self.image.height() * self.scale_factor),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.setPixmap(scaled_image)
            self.setFixedSize(scaled_image.size())  # 保持 QLabel 大小和图像一致
            
            # Update scrollbars if needed
            if self.parent() and isinstance(self.parent(), QScrollArea):
                self.parent().setWidgetResizable(False)

    def mouseMoveEvent(self, event):
        if self.pan_enabled and self.image:
            delta = event.pos() - self.last_pan_pos
            self.last_pan_pos = event.pos()
            
            # 打印出父对象的类型，找出正确的层级关系
            # parent = self.parent()
            # print(f"Parent type: {type(parent)}")
            
            # 直接使用保存的scroll_area引用而不是通过parent()查找
            # 在QLabel初始化时我们应已经保存了scroll_area的引用
            if hasattr(self, 'mainWindow'):
                if self == self.mainWindow.image_label1:
                    scroll_area = self.mainWindow.scroll_area1
                    # print("Using scroll_area1")
                elif self == self.mainWindow.image_label2:
                    scroll_area = self.mainWindow.scroll_area2
                    # print("Using scroll_area2")
                else:
                    scroll_area = None
                    
                if scroll_area:
                    # 现在我们有了正确的滚动区域引用
                    hbar = scroll_area.horizontalScrollBar()
                    vbar = scroll_area.verticalScrollBar()
                    
                    # 保存当前值用于调试
                    old_h = hbar.value()
                    old_v = vbar.value()
                    
                    # 设置新的滚动位置
                    hbar.setValue(old_h - delta.x())
                    vbar.setValue(old_v - delta.y())
                    
                    # print(f"Setting scrollbars: {old_h}->{hbar.value()}, {old_v}->{vbar.value()}") # 打印出滚动条的值
            
            # Sync scroll position with paired widget
            if self.paired_scroll_area:
                paired_vbar = self.paired_scroll_area.verticalScrollBar()
                paired_hbar = self.paired_scroll_area.horizontalScrollBar()
                paired_hbar.setValue(paired_hbar.value() - delta.x())
                paired_vbar.setValue(paired_vbar.value() - delta.y())
            
            self.update()
        else:
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton and self.image:
            self.pan_enabled = True
            self.last_pan_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        elif event.button() == Qt.LeftButton and self.mainWindow and not self.mainWindow.check_button.isChecked():
            # 计算图像原始坐标
            # 获取鼠标相对于QLabel的坐标
            pos = event.pos()
            
            # 获取滚动区域的滚动位置
            scroll_x = self.parent().horizontalScrollBar().value() if isinstance(self.parent(), QScrollArea) else 0
            scroll_y = self.parent().verticalScrollBar().value() if isinstance(self.parent(), QScrollArea) else 0
            
            # 将坐标转换回原图坐标系
            raw_x = pos.x() / self.scale_factor
            raw_y = pos.y() / self.scale_factor
            
            # 检查是否在图像范围内 - 使用正确的图像尺寸比较
            if self.image and 0 <= raw_x < self.image.width() and 0 <= raw_y < self.image.height():
                # 分别处理左图和右图的点击
                if self == self.mainWindow.image_label1 and self.mainWindow.left_turn:
                    self.mainWindow.add_point_to_left(QPoint(int(raw_x), int(raw_y)))
                elif self == self.mainWindow.image_label2 and not self.mainWindow.left_turn:
                    self.mainWindow.add_point_to_right(QPoint(int(raw_x), int(raw_y)))
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self.pan_enabled = False
            self.setCursor(Qt.ArrowCursor)

    def wheelEvent(self, event):
        if self.image:
            # Calculate mouse position relative to original image
            mouse_pos = event.pos()
            scroll_x = self.parent().horizontalScrollBar().value() if isinstance(self.parent(), QScrollArea) else 0
            scroll_y = self.parent().verticalScrollBar().value() if isinstance(self.parent(), QScrollArea) else 0
            
            # Get position in image coordinates
            rel_x = (mouse_pos.x() + scroll_x) / self.scale_factor
            rel_y = (mouse_pos.y() + scroll_y) / self.scale_factor
            
            # Determine zoom direction
            factor = 1.25 if event.angleDelta().y() > 0 else 0.8
            old_scale = self.scale_factor
            self.scale_factor *= factor
            
            # Keep scale factor within reasonable bounds
            self.scale_factor = max(0.1, min(10.0, self.scale_factor))
            
            # Update display
            self.update_display()
            
            # Calculate new scroll positions
            new_scroll_x = rel_x * self.scale_factor - mouse_pos.x()
            new_scroll_y = rel_y * self.scale_factor - mouse_pos.y()
            
            # Adjust scroll position to keep mouse position centered
            if isinstance(self.parent(), QScrollArea):
                self.parent().horizontalScrollBar().setValue(int(new_scroll_x))
                self.parent().verticalScrollBar().setValue(int(new_scroll_y))
            
            # Sync with paired label if exists
            if self.paired_label and self.paired_label.image:
                self.paired_label.scale_factor = self.scale_factor
                self.paired_label.update_display()
                
                if self.paired_scroll_area:
                    self.paired_scroll_area.horizontalScrollBar().setValue(int(new_scroll_x))
                    self.paired_scroll_area.verticalScrollBar().setValue(int(new_scroll_y))

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        
        pen = QPen(QColor(255, 0, 0), 3)
        painter.setPen(pen)
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        if not self.checkMode:
            for idx, point in enumerate(self.points):
                x = point.x() * self.scale_factor
                y = point.y() * self.scale_factor
                painter.drawEllipse(QPoint(int(x), int(y)), 4, 4)
                painter.setPen(QColor(255, 105, 180))
                painter.drawText(int(x + 5), int(y + 5), str(idx))
                painter.setPen(QPen(QColor(255, 0, 0), 3))
        elif len(self.points):
            x = self.points[self.checking].x() * self.scale_factor
            y = self.points[self.checking].y() * self.scale_factor
            painter.drawEllipse(QPoint(int(x), int(y)), 4, 4)
            painter.setPen(QColor(255, 105, 180))
            painter.drawText(int(x + 5), int(y + 5), str(self.checking))
            painter.setPen(QPen(QColor(255, 0, 0), 3))

        # Draw crosshair
        if self.underMouse() and not self.checkMode:
            cursor_pos = self.mapFromGlobal(self.cursor().pos())
            painter.setPen(QPen(Qt.green, 1, Qt.DashLine))
            painter.drawLine(0, cursor_pos.y(), self.width(), cursor_pos.y())
            painter.drawLine(cursor_pos.x(), 0, cursor_pos.x(), self.height())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("image/mylogo.ico"))
        self.setWindowTitle("图像配准标注器")
        self.resize(1200, 800)

        self.opt_dir = ""
        self.sar_dir = ""
        self.image_list = []
        self.current_index = 0

        self.left_turn = True
        self.save_dir = ""
        
        # 保存原始点集，用于比较是否有变化
        self.original_points1 = []
        self.original_points2 = []

        # Create scroll areas for image labels
        self.scroll_area1 = QScrollArea()
        self.scroll_area1.setWidgetResizable(True)
        self.scroll_area1.setMinimumSize(500, 500)
        self.scroll_area1.setAlignment(Qt.AlignCenter)
        
        self.scroll_area2 = QScrollArea()
        self.scroll_area2.setWidgetResizable(True)
        self.scroll_area2.setMinimumSize(500, 500)
        self.scroll_area2.setAlignment(Qt.AlignCenter)
        
        # Create image labels
        self.image_label1 = ImageLabel()
        self.image_label2 = ImageLabel()
        
        # 关联主窗口到标签
        self.image_label1.mainWindow = self
        self.image_label2.mainWindow = self
        
        # Set scroll areas to contain the labels
        self.scroll_area1.setWidget(self.image_label1)
        self.scroll_area2.setWidget(self.image_label2)
        
        # Link the two image labels together
        self.image_label1.paired_label = self.image_label2
        self.image_label2.paired_label = self.image_label1
        
        # Link scroll areas
        self.image_label1.paired_scroll_area = self.scroll_area2
        self.image_label2.paired_scroll_area = self.scroll_area1
        
        self.saved = True

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入图片名并回车定位...例如(0_0)")
        self.search_input.returnPressed.connect(self.search_image)

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        hbox = QHBoxLayout()

        hbox.addWidget(self.scroll_area1)
        hbox.addWidget(self.scroll_area2)

        button_layout = QHBoxLayout()
        self.load_button = QPushButton("打开图片夹")
        self.load_button.clicked.connect(self.load_images)
        button_layout.addWidget(self.load_button)

        self.prev_button = QPushButton("上一张")
        self.prev_button.clicked.connect(self.prev_image)
        button_layout.addWidget(self.prev_button)

        self.next_button = QPushButton("下一张")
        self.next_button.clicked.connect(self.next_image)
        button_layout.addWidget(self.next_button)

        self.save_button = QPushButton("保存标注")
        self.save_button.clicked.connect(self.save_points_to_csv)
        button_layout.addWidget(self.save_button)

        self.set_dir_button = QPushButton("设置保存目录")
        self.set_dir_button.clicked.connect(self.set_save_directory)
        button_layout.addWidget(self.set_dir_button)

        button_layout.addWidget(self.search_input)

        check_layout = QHBoxLayout()
        self.check_button = QPushButton("检查模式")
        self.check_button.setCheckable(True)
        self.check_button.setEnabled(False)
        check_layout.addWidget(self.check_button)
        self.check_button.clicked.connect(self.__check_mode)

        self.check_prev_button = QPushButton("上一对")
        self.check_prev_button.setEnabled(False)
        check_layout.addWidget(self.check_prev_button)
        self.check_prev_button.clicked.connect(self.__check_prev)

        self.check_next_button = QPushButton("下一对")
        self.check_next_button.setEnabled(False)
        check_layout.addWidget(self.check_next_button)
        self.check_next_button.clicked.connect(self.__check_next)

        self.delete_button = QPushButton("删除")
        self.delete_button.setEnabled(False)
        check_layout.addWidget(self.delete_button)
        self.delete_button.clicked.connect(self.__delete)

        layout.addLayout(hbox)
        layout.addLayout(button_layout)
        layout.addLayout(check_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def load_images(self):
        self.opt_dir = QFileDialog.getExistingDirectory(self, "选择OPT文件夹")
        self.sar_dir = QFileDialog.getExistingDirectory(self, "选择SAR文件夹")
        if not self.opt_dir or not self.sar_dir:
            return
        # 根据文件修改时间排序
        self.image_list = sorted(
            list(set(os.listdir(self.opt_dir)).intersection(set(os.listdir(self.sar_dir)))),
            key=lambda x: os.path.getmtime(os.path.join(self.opt_dir, x))
        )
        self.current_index = 0
        self.load_current_image()
        self.check_button.setEnabled(True)

    def load_current_image(self):
        if not self.image_list:
            return

        filename = self.image_list[self.current_index]
        opt_path = os.path.join(self.opt_dir, filename)
        sar_path = os.path.join(self.sar_dir, filename)

        # Reset zoom and pan for both images
        self.image_label1.scale_factor = 1.0
        self.image_label2.scale_factor = 1.0
        
        # Reset scrollbar positions
        self.scroll_area1.horizontalScrollBar().setValue(0)
        self.scroll_area1.verticalScrollBar().setValue(0)
        self.scroll_area2.horizontalScrollBar().setValue(0)
        self.scroll_area2.verticalScrollBar().setValue(0)
        
        self.image_label1.set_image(QPixmap(opt_path))
        self.image_label2.set_image(QPixmap(sar_path))
        self.image_label1.points.clear()
        self.image_label2.points.clear()
        
        # 清除原始点集
        self.original_points1.clear()
        self.original_points2.clear()

        # 自动加载对应的CSV坐标标注
        if self.save_dir:
            csv_name = os.path.splitext(filename)[0] + "_points.csv"
            csv_path = os.path.join(self.save_dir, csv_name)
            if os.path.exists(csv_path):
                try:
                    with open(csv_path, 'r', newline='') as file:
                        reader = csv.reader(file)
                        rows = list(reader)

                        # 自动跳过前几行标题
                        start_idx = 0
                        for i, row in enumerate(rows):
                            if row and row[0] == 'ID':
                                start_idx = i + 1
                                break

                        for row in rows[start_idx:]:
                            if len(row) >= 5:
                                x1, y1, x2, y2 = map(int, row[1:5])
                                self.image_label1.points.append(QPoint(x1, y1))
                                self.image_label2.points.append(QPoint(x2, y2))
                                # 保存原始点集
                                self.original_points1.append(QPoint(x1, y1))
                                self.original_points2.append(QPoint(x2, y2))
                except Exception as e:
                    QMessageBox.warning(self, "读取标注失败", f"无法读取标注文件：\n{str(e)}")

        self.image_label1.update()
        self.image_label2.update()
        self.left_turn = True
        self.setWindowTitle(f"图像配准标注器 - 当前图片: {filename}")
        
        # 重置保存状态
        self.saved = True

    def search_image(self):
        target_name = self.search_input.text().strip()
        target_name = 'tile_' + target_name + '.png'
        if not target_name:
            return
        if target_name not in self.image_list:
            QMessageBox.warning(self, "未找到图片", f"未找到名为 {target_name} 的图片。")
            return
        self.current_index = self.image_list.index(target_name)
        self.load_current_image()

    def next_image(self):
        # 只在点集有变化且未保存时提示保存
        if not self.saved and self.points_changed():
            msg = QMessageBox(self)
            msg.setWindowTitle("未保存")
            msg.setText("当前标注结果尚未保存，是否继续？")
            msg.setIcon(QMessageBox.Warning)

            save_button = msg.addButton("保存", QMessageBox.YesRole)
            continue_button = msg.addButton("不保存，继续", QMessageBox.NoRole)
            cancel_button = msg.addButton("取消", QMessageBox.RejectRole)

            msg.exec_()

            clicked_button = msg.clickedButton()

            if clicked_button == save_button:
                self.save_points_to_csv()  # 保存当前标注
            elif clicked_button == cancel_button:
                return
            # 如果点击了"不保存，继续"，什么都不做，直接继续

        if self.current_index < len(self.image_list) - 1:
            self.current_index += 1
            self.load_current_image()

    def prev_image(self):
        # 只在点集有变化且未保存时提示保存
        if not self.saved and self.points_changed():
            msg = QMessageBox(self)
            msg.setWindowTitle("未保存")
            msg.setText("当前标注结果尚未保存，是否继续？")
            msg.setIcon(QMessageBox.Warning)

            save_button = msg.addButton("保存", QMessageBox.YesRole)
            continue_button = msg.addButton("不保存，继续", QMessageBox.NoRole)
            cancel_button = msg.addButton("取消", QMessageBox.RejectRole)

            msg.exec_()

            clicked_button = msg.clickedButton()

            if clicked_button == save_button:
                self.save_points_to_csv()  # 保存当前标注
            elif clicked_button == cancel_button:
                return
            # 如果点击了"不保存，继续"，什么都不做，直接继续

        if self.current_index > 0:
            self.current_index -= 1
            self.load_current_image()

    def set_save_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "选择保存目录")
        if dir_path:
            self.save_dir = dir_path

    def save_points_to_csv(self):
        if len(self.image_label1.points) != len(self.image_label2.points):
            QMessageBox.warning(self, "保存失败", "左右图像标注的点数不一致，无法保存！")
            return

        if not self.save_dir:
            QMessageBox.warning(self, "保存失败", "尚未设置保存目录！")
            return

        filename = self.image_list[self.current_index]
        save_name = os.path.splitext(filename)[0] + "_points.csv"
        save_path = os.path.join(self.save_dir, save_name)

        with open(save_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([f"LeftImage: OPT/{filename}"])
            writer.writerow([f"RightImage: SAR/{filename}"])
            writer.writerow(["-" * 50])
            writer.writerow(["ID", "LeftX", "LeftY", "RightX", "RightY"])
            for i, (p1, p2) in enumerate(zip(self.image_label1.points, self.image_label2.points), start=1):
                writer.writerow([i, int(p1.x()), int(p1.y()), int(p2.x()), int(p2.y())])

        self.saved = True
        
        # 保存当前点集为原始点集
        self.original_points1 = self.image_label1.points.copy()
        self.original_points2 = self.image_label2.points.copy()
        
        QMessageBox.information(self, "保存成功", f"标注点已保存至 {save_path}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Right:
            self.next_image()
        elif event.key() == Qt.Key_Left:
            self.prev_image()
        elif event.key() == Qt.Key_S and event.modifiers() & Qt.ControlModifier:
            self.save_points_to_csv()
        elif event.key() == Qt.Key_Z and event.modifiers() & Qt.ControlModifier:
            if self.image_label1.points and self.image_label2.points:
                if len(self.image_label1.points) > len(self.image_label2.points):
                    self.image_label1.points.pop()
                elif len(self.image_label2.points) > len(self.image_label1.points):
                    self.image_label2.points.pop()
                else:
                    self.image_label1.points.pop()
                    self.image_label2.points.pop()
                self.image_label1.update()
                self.image_label2.update()

    def mousePressEvent(self, event):
        if not self.check_button.isChecked():
            if event.button() == Qt.LeftButton:
                pos = self.mapFromGlobal(event.globalPos())
                
                # Check if click is in scroll area 1
                scroll_pos1 = self.scroll_area1.mapFromParent(pos)
                if self.scroll_area1.rect().contains(scroll_pos1) and self.left_turn:
                    # Convert to ImageLabel coordinates
                    local_pos = self.image_label1.mapFrom(self.scroll_area1, scroll_pos1)
                    
                    # Consider scrollbar positions
                    scroll_x = self.scroll_area1.horizontalScrollBar().value()
                    scroll_y = self.scroll_area1.verticalScrollBar().value()
                    
                    # Adjust position with scroll
                    local_pos.setX(local_pos.x() + scroll_x)
                    local_pos.setY(local_pos.y() + scroll_y)
                    
                    # Convert to original image coordinates
                    raw_x = local_pos.x() / self.image_label1.scale_factor
                    raw_y = local_pos.y() / self.image_label1.scale_factor
                    
                    # Check if the point is within the image
                    if 0 <= raw_x < self.image_label1.image.width() / self.image_label1.scale_factor and \
                       0 <= raw_y < self.image_label1.image.height() / self.image_label1.scale_factor:
                        mapped_point = QPoint(int(raw_x), int(raw_y))
                        self.image_label1.points.append(mapped_point)
                        self.image_label1.update()
                        self.left_turn = False
                        self.saved = False
                
                # Check if click is in scroll area 2
                scroll_pos2 = self.scroll_area2.mapFromParent(pos)
                if self.scroll_area2.rect().contains(scroll_pos2) and not self.left_turn:
                    # Convert to ImageLabel coordinates
                    local_pos = self.image_label2.mapFrom(self.scroll_area2, scroll_pos2)
                    
                    # Consider scrollbar positions
                    scroll_x = self.scroll_area2.horizontalScrollBar().value()
                    scroll_y = self.scroll_area2.verticalScrollBar().value()
                    
                    # Adjust position with scroll
                    local_pos.setX(local_pos.x() + scroll_x)
                    local_pos.setY(local_pos.y() + scroll_y)
                    
                    # Convert to original image coordinates
                    raw_x = local_pos.x() / self.image_label2.scale_factor
                    raw_y = local_pos.y() / self.image_label2.scale_factor
                    
                    # Check if the point is within the image
                    if 0 <= raw_x < self.image_label2.image.width() / self.image_label2.scale_factor and \
                       0 <= raw_y < self.image_label2.image.height() / self.image_label2.scale_factor:
                        mapped_point = QPoint(int(raw_x), int(raw_y))
                        self.image_label2.points.append(mapped_point)
                        self.image_label2.update()
                        self.left_turn = True
                        self.saved = False

    def __check_mode(self):
        if self.check_button.isChecked():
            if self.image_label1.checking < len(self.image_label1.points) - 1:
                self.check_next_button.setEnabled(True)
            if len(self.image_label1.points):
                self.delete_button.setEnabled(True)

            self.image_label1.checking = 0
            self.image_label2.checking = 0

            self.image_label1.checkMode = True
            self.image_label2.checkMode = True

            self.image_label1.update()
            self.image_label2.update()

        else:
            self.check_prev_button.setEnabled(False)
            self.check_next_button.setEnabled(False)

            self.image_label1.checkMode = False
            self.image_label2.checkMode = False

            self.image_label1.update()
            self.image_label2.update()

    def __check_next(self):
        self.image_label1.checking += 1
        self.image_label2.checking += 1
        self.image_label1.update()
        self.image_label2.update()
        self.check_prev_button.setEnabled(True)
        if self.image_label1.checking >= len(self.image_label1.points) - 1:
            self.check_next_button.setEnabled(False)

    def __check_prev(self):
        self.image_label1.checking -= 1
        self.image_label2.checking -= 1
        self.image_label1.update()
        self.image_label2.update()
        self.check_next_button.setEnabled(True)
        if not self.image_label1.checking:
            self.check_prev_button.setEnabled(False)

    def __delete(self):
        self.image_label1.points.pop(self.image_label1.checking)
        self.image_label2.points.pop(self.image_label2.checking)

        if self.image_label1.checking:
            self.image_label1.checking -= 1
            self.image_label2.checking -= 1

        if len(self.image_label1.points) == 0:
            self.delete_button.setEnabled(False)

        if self.image_label1.checking >= len(self.image_label1.points) - 1:
            self.check_next_button.setEnabled(False)

        if not self.image_label1.checking:
            self.check_prev_button.setEnabled(False)

        self.image_label1.update()
        self.image_label2.update()

    # 添加新方法用于从子控件中添加点
    def add_point_to_left(self, point):
        self.image_label1.points.append(point)
        self.image_label1.update()
        self.left_turn = False
        self.saved = False
        
    def add_point_to_right(self, point):
        self.image_label2.points.append(point)
        self.image_label2.update()
        self.left_turn = True
        self.saved = False

    # 判断点集是否有变化
    def points_changed(self):
        # 数量不同则肯定有变化
        if len(self.image_label1.points) != len(self.original_points1) or len(self.image_label2.points) != len(self.original_points2):
            return True
            
        # 比较每个点是否有变化
        for i in range(len(self.image_label1.points)):
            if self.image_label1.points[i] != self.original_points1[i] or self.image_label2.points[i] != self.original_points2[i]:
                return True
                
        return False


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

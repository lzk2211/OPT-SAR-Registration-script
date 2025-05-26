import sys
import os
import csv
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QPushButton, QFileDialog,
                             QHBoxLayout, QVBoxLayout, QWidget, QMessageBox)
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtWidgets import QScrollArea, QLineEdit
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtGui import QIcon

from PIL import Image


class ImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.points = []
        self.scale_factor = 1.0  # 缩放因子
        self.image = None
        self.index = 0
        self.setMouseTracking(True)
        self.setAlignment(Qt.AlignLeft | Qt.AlignTop)

    def set_image(self, image):
        self.image = image
        self.update_display()

    def update_display(self):
        if self.image:
            scaled_image = self.image.scaled(
                self.image.width() * self.scale_factor,
                self.image.height() * self.scale_factor,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.setPixmap(scaled_image)
            self.setFixedSize(scaled_image.size())  # 保持 QLabel 大小和图像一致

    def mouseMoveEvent(self, event):
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        pen = QPen(QColor(255, 0, 0), 3)
        painter.setPen(pen)
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        for idx, point in enumerate(self.points):
            x = point.x() * self.scale_factor
            y = point.y() * self.scale_factor
            painter.drawEllipse(QPoint(int(x), int(y)), 4, 4)
            painter.setPen(QColor(255, 105, 180))
            painter.drawText(int(x + 5), int(y + 5), str(idx))
            painter.setPen(QPen(QColor(255, 0, 0), 3))

        # Draw crosshair
        if self.underMouse():
            cursor_pos = self.mapFromGlobal(self.cursor().pos())
            painter.setPen(QPen(Qt.green, 1, Qt.DashLine))
            painter.drawLine(0, cursor_pos.y(), self.width(), cursor_pos.y())
            painter.drawLine(cursor_pos.x(), 0, cursor_pos.x(), self.height())

    def wheelEvent(self, event):
        # 滚轮缩放
        if self.image:
            delta = event.angleDelta().y()
            if delta > 0:
                self.scale_factor *= 1.1
            else:
                self.scale_factor /= 1.1
            self.update_display()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("mylogo.ico"))
        self.setWindowTitle("图像配准标注器")
        self.resize(1200, 800)

        self.opt_dir = ""
        self.sar_dir = ""
        self.image_list = []
        self.current_index = 0

        self.left_turn = True
        self.save_dir = ""

        self.image_label1 = ImageLabel()
        self.image_label2 = ImageLabel()
        self.saved = True

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入图片名并回车定位...")
        self.search_input.returnPressed.connect(self.search_image)

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        hbox = QHBoxLayout()

        hbox.addWidget(self.image_label1)
        hbox.addWidget(self.image_label2)

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

        self.import_button = QPushButton("导入标注")
        self.import_button.clicked.connect(self.import_points_from_csv)
        button_layout.addWidget(self.import_button)

        button_layout.addWidget(self.search_input)

        layout.addLayout(hbox)
        layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.image_label1.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.image_label2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    def import_points_from_csv(self):
        csv_path, _ = QFileDialog.getOpenFileName(self, "选择标注文件", "", "CSV Files (*.csv)")
        if not csv_path:
            return

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

                self.image_label1.points.clear()
                self.image_label2.points.clear()
                for row in rows[start_idx:]:
                    if len(row) >= 5:
                        x1, y1, x2, y2 = map(int, row[1:5])
                        self.image_label1.points.append(QPoint(x1, y1))
                        self.image_label2.points.append(QPoint(x2, y2))

            self.image_label1.update()
            self.image_label2.update()
            self.saved = False
            QMessageBox.information(self, "导入成功", "标注点已成功导入并显示。")
        except Exception as e:
            QMessageBox.warning(self, "导入失败", f"无法导入标注文件：\n{str(e)}")

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

    def load_current_image(self):
        if not self.image_list:
            return

        filename = self.image_list[self.current_index]
        opt_path = os.path.join(self.opt_dir, filename)
        sar_path = os.path.join(self.sar_dir, filename)

        self.image_label1.set_image(QPixmap(opt_path))
        self.image_label2.set_image(QPixmap(sar_path))
        self.image_label1.points.clear()
        self.image_label2.points.clear()

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
                except Exception as e:
                    QMessageBox.warning(self, "读取标注失败", f"无法读取标注文件：\n{str(e)}")

        self.image_label1.update()
        self.image_label2.update()
        self.left_turn = True
        self.setWindowTitle(f"图像配准标注器 - 当前图片: {filename}")

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
        if not self.saved:
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
                self.save_current()  # 调用保存函数（请确保你有这个函数）
            elif clicked_button == cancel_button:
                return
            # 如果点击了“不保存，继续”，什么都不做，直接继续

        if self.current_index < len(self.image_list) - 1:
            self.current_index += 1
            self.load_current_image()

    def prev_image(self):
        if not self.saved:
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
                self.save_current()  # 调用保存函数（请确保你有这个函数）
            elif clicked_button == cancel_button:
                return
            # 如果点击了“不保存，继续”，什么都不做，直接继续

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
                self.image_label1.points.pop()
                self.image_label2.points.pop()
                self.image_label1.update()
                self.image_label2.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = self.mapFromGlobal(event.globalPos())
            label1_geom = self.image_label1.geometry()
            label2_geom = self.image_label2.geometry()

            if label1_geom.contains(pos) and self.left_turn:
                local_pos = self.image_label1.mapFromParent(pos)
                mapped_point = QPoint(local_pos.x() / self.image_label1.scale_factor,
                                      local_pos.y() / self.image_label1.scale_factor)
                self.image_label1.points.append(mapped_point)
                self.image_label1.update()
                self.left_turn = False
                self.saved = False

            elif label2_geom.contains(pos) and not self.left_turn:
                local_pos = self.image_label2.mapFromParent(pos)
                mapped_point = QPoint(local_pos.x() / self.image_label2.scale_factor,
                                      local_pos.y() / self.image_label2.scale_factor)
                self.image_label2.points.append(mapped_point)
                self.image_label2.update()
                self.left_turn = True
                self.saved = False


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
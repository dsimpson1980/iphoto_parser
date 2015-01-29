import sys
import os
import logging
import collections
from PyQt4 import QtGui, QtCore

import sorter


class QtHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)

    def emit(self, record):
        record = self.format(record)
        if record: XStream.stdout().write('%s\n' % record)
        # originally: XStream.stdout().write("{}\n".format(record))


class XStream(QtCore.QObject):
    _stdout = None
    _stderr = None
    messageWritten = QtCore.pyqtSignal(str)

    def flush(self):
        pass

    def fileno(self):
        return -1

    def write(self, msg):
        if (not self.signalsBlocked()):
            self.messageWritten.emit(unicode(msg))

    @staticmethod
    def stdout():
        if (not XStream._stdout):
            XStream._stdout = XStream()
            sys.stdout = XStream._stdout
        return XStream._stdout

    @staticmethod
    def stderr():
        if (not XStream._stderr):
            XStream._stderr = XStream()
            sys.stderr = XStream._stderr
        return XStream._stderr


class SorterGUI(QtGui.QMainWindow):

    def __init__(self):
        super(SorterGUI, self).__init__()
        self.initUI()

    def initUI(self):

        self.setToolTip('This is a <b>QWidget</b> widget')
        self.setCentralWidget(MyWidget())
        self.setGeometry(300, 300, 600, 400)
        self.setWindowTitle('Tooltips')
        self.show()


class MyWidget(QtGui.QWidget):
    def __init__(self):
        source_path = os.path.expanduser('~/Pictures/iPhoto Library.photolibrary')
        target_dir = os.path.expanduser('~/Pictures/parser_output')
        self.filter_by_model = QtGui.QCheckBox('Filter by Model')

        QtGui.QWidget.__init__(self)
        self.source_qle = QtGui.QLineEdit(self)
        self.source_qle.setText(source_path)
        source_btn = QtGui.QPushButton('Source', self)
        source_btn.setToolTip('Select an iphoto library to parse')
        source_btn.resize(source_btn.sizeHint())
        source_btn.clicked.connect(self.select_lib)
        source_hbox = QtGui.QHBoxLayout()
        source_hbox.stretch(1)
        source_hbox.addWidget(source_btn)
        source_hbox.addWidget(self.source_qle)

        self.target_qle = QtGui.QLineEdit(self)
        self.target_qle.setText(target_dir)
        target_btn = QtGui.QPushButton('Target', self)
        target_btn.setToolTip('Select target directory')
        target_btn.resize(target_btn.sizeHint())
        target_btn.clicked.connect(self.select_target)
        target_hbox = QtGui.QHBoxLayout()
        target_hbox.addWidget(target_btn)
        target_hbox.addWidget(self.target_qle)

        self._console = QtGui.QTextBrowser(self)

        parse_btn = QtGui.QPushButton('Parse!', self)
        parse_btn.setToolTip('Parse selected iphoto library')
        parse_btn.resize(parse_btn.sizeHint())
        parse_btn.clicked.connect(self.parse_lib)

        quit_btn = QtGui.QPushButton('Quit', self)
        quit_btn.setToolTip('Quit iphoto parser')
        quit_btn.resize(quit_btn.sizeHint())
        quit_btn.clicked.connect(QtCore.QCoreApplication.instance().quit)

        vbox = QtGui.QVBoxLayout()
        vbox.addStretch(1)
        vbox.addLayout(source_hbox)
        vbox.addLayout(target_hbox)
        vbox.addWidget(self.filter_by_model)
        vbox.addWidget(self._console)
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(parse_btn)
        hbox.addWidget(quit_btn)
        vbox.addLayout(hbox)

        self.setLayout(vbox)

        XStream.stdout().messageWritten.connect(self.write_log)
        XStream.stderr().messageWritten.connect(self.write_log)

        # Thread
        self.bee = Worker(self.someProcess, ())
        self.bee.finished.connect(self.restoreUi)
        self.bee.terminated.connect(self.restoreUi)

    def write_log(self, str):
        self._console.insertPlainText(str)
        self._console.moveCursor(QtGui.QTextCursor.End)

    def someProcess(self):
        fields = ['source_path', 'export_dir', 'filter_by_model']
        Args = collections.namedtuple('Args', fields)
        args = Args(str(self.source_qle.text()), str(self.target_qle.text()),
                    self.filter_by_model.isChecked())
        sorter.parse_files(args)

    def restoreUi(self):
        self.button.setEnabled(True)

    def parse_lib(self):
        self.bee.start()

    def select_lib(self):
        filepath = QtGui.QFileDialog.getOpenFileName(
            self, 'Open file', self.source_qle.text())
        self.source_qle.setText(filepath)
        logging.info('Set libpath to %s', self.source_qle.text())

    def select_target(self):
        dirpath = QtGui.QFileDialog.getExistingDirectory(
            self, 'Select USB Drive Location', self.target_qle.text())
        self.target_qle.setText(dirpath)
        logging.info('Set target directory to %s', self.source_qle.text())


class Worker(QtCore.QThread):
    def __init__(self, func, args):
        super(Worker, self).__init__()
        self.func = func
        self.args = args

    def run(self):
        self.func(*self.args)


def MainWindow(app):
    sys.exit(app.exec_())


def main():
    app = QtGui.QApplication(sys.argv)
    sorter_gui = SorterGUI()
    main_app = MainWindow(app)
    main_app.show()
    main_app.raise_()

if __name__ == '__main__':
    logging.basicConfig(level='INFO')
    handler = QtHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logging.basicConfig(level='INFO')
    logging.getLogger('').addHandler(handler)
    main()
import os
import pymel.core as pm
import pymel.api as pma
from PySide2 import QtWidgets
from PySide2 import QtCore

from sl_history.logger import Logger
from sl_history.config import Config
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from shiboken2 import getCppPointer


def add_widget_to_layout(widget, control_name):
    if pm.workspaceControl(control_name, q=1, ex=1):
        if os.sys.version_info[0] >= 3:
            workspaceControlPtr = int(pma.MQtUtil.findControl(control_name))
            widgetPtr = int(getCppPointer(widget)[0])
        else:
            workspaceControlPtr = long(pma.MQtUtil.findControl(control_name))
            widgetPtr = long(getCppPointer(widget)[0])

        pma.MQtUtil.addWidgetToMayaLayout(widgetPtr, workspaceControlPtr)


class Dialog(MayaQWidgetDockableMixin, QtWidgets.QWidget):

    WINDOW_TITLE = "sl_history"
    UI_NAME = "sl_history"
    UI_SCRIPT = "import sl_history\nsl_history_dialog = sl_history.Dialog()"
    LOG_FILE = os.path.join(pm.moduleInfo(mn="sl_history", p=1), "sl_history.log")  # type:str
    UI_INSTANCE = None
    MIN_WIDGTH = 200
    MIN_HEIGHT = 100
    SCRIPT_JOB = 0

    @ classmethod
    def display(cls):
        if not cls.UI_INSTANCE:
            cls.UI_INSTANCE = Dialog()

        if cls.UI_INSTANCE.isHidden():
            cls.UI_INSTANCE.show(dockable=1, uiScript=cls.UI_SCRIPT)
        else:
            cls.UI_INSTANCE.raise_()
            cls.UI_INSTANCE.activateWindow()

    def __init__(self):
        super(Dialog, self).__init__()

        self.__class__.UI_INSTANCE = self
        self.setObjectName(self.__class__.UI_NAME)
        self.setWindowTitle(self.WINDOW_TITLE)

        self.workspaceControlName = "{0}WorkspaceControl".format(self.UI_NAME)
        add_widget_to_layout(self, self.workspaceControlName)

        # Init fields and config
        Logger.set_level(Config.get("logging.level", default=20))
        Logger.write_to_rotating_file(self.LOG_FILE)

        # Setup context menu
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        # UI setup
        self.create_actions()
        self.create_widgets()
        self.create_layouts()
        self.create_connections()

    def create_actions(self):
        self.clear_history_action = QtWidgets.QAction("Clear", self)

    def create_widgets(self):
        self.history_list = QtWidgets.QListWidget()

    def create_layouts(self):
        history_layout = QtWidgets.QVBoxLayout()
        history_layout.addWidget(self.history_list)

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(history_layout)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

    def create_connections(self):
        self.history_list.itemClicked.connect(self.on_item_selected)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.clear_history_action.triggered.connect(self.history_list.clear)

    def show_context_menu(self, point):
        contextMenu = QtWidgets.QMenu()
        contextMenu.addAction(self.clear_history_action)

        contextMenu.exec_(self.mapToGlobal(point))

    def _create_job(self):
        if not self.SCRIPT_JOB:
            self.SCRIPT_JOB = pm.scriptJob(e=("SelectionChanged", self.update_selection_list))  # type: int

    def _kill_job(self):
        if self.SCRIPT_JOB:
            pm.scriptJob(k=self.SCRIPT_JOB, f=1)
            self.SCRIPT_JOB = 0

    def on_item_selected(self, item):
        selection_list = item.data(1)
        self._kill_job()
        pm.select([obj for obj in selection_list if pm.objExists(obj)])
        self._create_job()

    def update_selection_list(self):
        sel = pm.ls(sl=1)
        if not sel or self.isHidden():
            return

        self.add_list_item([str(obj) for obj in sel])

    def add_list_item(self, all_items):
        if self.history_list.count() and all_items == self.history_list.item(0).data(1):
            return

        # Else create new item
        new_list_item = QtWidgets.QListWidgetItem()
        if len(all_items) > 4:
            new_list_item.setText("..." + str(all_items[-4:]))
        else:
            new_list_item.setText(str(all_items))

        new_list_item.setToolTip(str(all_items))
        new_list_item.setData(1, all_items)
        self.history_list.insertItem(0, new_list_item)

        # Delete oldest item
        if self.history_list.count() > Config.get("history.size"):
            self.history_list.takeItem(self.history_list.count() - 1)

    # Events
    def showEvent(self, event):
        if not self.SCRIPT_JOB:
            self._create_job()

    def closeEvent(self, e):
        self._kill_job()

    def dockCloseEventTriggered(self):
        super(Dialog, self).dockCloseEventTriggered()
        self._kill_job()


if __name__ == "__main__":
    try:
        if sl_history_dialog and sl_history_dialog.parent():  # noqa: F821
            workspaceControlName = sl_history_dialog.parent().objectName()  # noqa: F821

            if pm.window(workspaceControlName, ex=1, q=1):
                pm.deleteUI(workspaceControlName)
    except Exception:
        pass

    sl_history_dialog = Dialog()
    sl_history_dialog.show(dockable=1, uiScript=Dialog.UI_SCRIPT)

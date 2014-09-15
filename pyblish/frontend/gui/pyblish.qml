import QtQuick 2.0
import QtQuick.Layouts 1.1
import Controller 1.0

import "../contents"
import "../utils"


Item {
    id: main
    // visible: false
    anchors.centerIn: parent
    width: parent.width
    height: parent.height
    property var list_names: []
    property var list_families: []
    property var list_docNames: []
    property var list_docConts: []
    MouseArea {
        anchors.fill: parent
        property real lastMouseX: 0
        property real lastMouseY: 0
        acceptedButtons: Qt.LeftButton
        onPressed: {
            if(mouse.button == Qt.LeftButton){
                parent.forceActiveFocus()
                lastMouseX = mouseX
                lastMouseY = mouseY
            }
        }
        onMouseXChanged: root.x += (mouseX - lastMouseX)
        onMouseYChanged: root.y += (mouseY - lastMouseY)
    }

    OuterBevelFrame {
        id: base
        width: parent.width
        height: parent.height
        // Rectangle {
        //     width: parent.width
        //     height: parent.height
        //     color: "green"
        // }

        ColumnLayout {
            id: ui
            width: parent.width
            height: parent.height
            spacing: 30
            Layout.alignment: Qt.AlignHCenter | Qt.AlignHCenter
            RowLayout {
                id: header
                // Layout.maximumHeight: 30
                Layout.maximumWidth: parent.width - 5
                Image {
                    id: logoIcon
                    source: "../contents/logo_32.png"
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.margins: 5
                    width: 8
                    height: 8
                    Text {
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.margins: 40
                        text: 'Pyblish'
                        color: '#58b2f7'
                        font.family: 'Consolas'
                        font.pixelSize: 13
                    }
                }

                ColumnLayout {
                    width: parent.width
                    Layout.alignment: Qt.AlignRight
                    RowLayout {
                        Image {
                            id: helpBg
                            source: "../contents/button_help.png"
                            MouseArea {
                                id: helpBtn
                                anchors.fill: parent
                                // onClicked: Qt.quit()
                            }
                        }
                        Image {
                            id: minimizeBg
                            source: "../contents/button_minimise.png"

                            MouseArea {
                                id: minimizeBtn
                                anchors.fill: parent
                                onClicked: root.visibility = Window.Minimized
                            }
                        }
                        Image {
                            id: closeBg
                            source: "../contents/button_close.png"
                            MouseArea {
                                id: closeBtn
                                anchors.fill: parent
                                onClicked: Qt.quit()
                            }
                        }
                    }
                }
            }
            RowLayout {
                id: page
                // Layout.maximumHeight: parent.height
                Layout.maximumWidth: parent.width 
                Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
                spacing: 0
                ColumnLayout {
                    Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
                    spacing: 10
                    Layout.minimumWidth: parent.width - 60
                    // Rectangle {
                    //  width: parent.width
                    //  height: parent.height
                    //     color: "transparent"
                    //  border.color: "black"

                    // }
                    RowLayout {
                        Text {
                            // anchors.centerIn: parent
                            Component.onCompleted: {
                                text = ('Instances... [ ' + getCount() + ' ]')
                            }
                            
                            color: '#fefefe'
                            font.family: 'Consolas'
                        }
                    }
                    RowLayout {
                        Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
                        // Layout.minimumHeight: parent.height - 50
                        InnerBevelFrame {
                            anchors.centerIn: parent
                            width: parent.width
                            height: parent.height
                            ListView {
                                id: lv
                                anchors.centerIn: parent
                                width: parent.width - 20
                                height: parent.height - 20
                                clip: true
                                // orientation: ListView.Vertical

                                model: list_names
                                spacing: 5

                                snapMode: ListView.SnapOneItem
                                delegate: ListItem {
                                }
                            }
                        }
                    }
                    RowLayout {
                        Layout.alignment: Qt.AlignHCenter | Qt.AlignVCenter
                        Content {}
                    }
                }
            }
        }
    }

    Controller {
        id: cont
        Component.onCompleted: {
            list_names = getName()
            list_families = getFamily()
            list_docNames = getDocName()
            list_docConts = getDocContent()
        }
    }

    function getCount() {
        return cont.lists.length
    }

    function getName() {
        var _list = []
        for(var i=0;i < cont.lists.length;i++){
            _list[i] = cont.lists[i].name
        }
        return _list
    }
    function getFamily() {
        var _list = []
        for(var i=0;i < cont.lists.length;i++){
            _list[i] = cont.lists[i].family
        }
        return _list
    }
    function getDocName() {
        var _list = []
        for(var i=0;i < cont.lists.length;i++){
            _list[i] = cont.lists[i].document_name
        }
        return _list
    }
    function getDocContent() {
        var _list = []
        for(var i=0;i < cont.lists.length;i++){
            _list[i] = cont.lists[i].document_content
        }
        return _list
    }
}
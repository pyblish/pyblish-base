import QtQuick 2.0
import QtQuick.Controls 1.0
import QtQuick.Controls.Styles 1.0
import QtQuick.Layouts 1.1

import "../contents"

Item {
    id: btnDelegate
    property string buttonColor: "#4b4b4b"
    property bool mainEnabled: true
    property alias iconVisibility: expandBg.visible
    property alias label: btnLabel.text
    property int textWidth: 0
    property int parentIndex
    signal clicked()
    height: 25
    width: 125
    enabled: mainEnabled

    OuterBevelFrame {
        id: buttonFrame
        bgColor: btnDelegate.buttonColor
        width: parent.width
        height: parent.height
        Text {
            id: btnLabel
            // anchors.left: parent.left
            // anchors.verticalCenter: parent.verticalCenter
            // anchors.leftMargin: 5
            anchors.centerIn: parent
            text: 'Default'
            color: '#fefefe'
            font.family: 'Consolas'
            Component.onCompleted: {
                textWidth = width
            }
        }
        Image {
            id: expandBg
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            anchors.margins: 3
            width: 16
            height: 16
            source: "../contents/button_expand.png"
        }

        MouseArea {
            id: buttonMouse
            anchors.fill: parent
            hoverEnabled: true
            onEntered: {
                buttonColor = "#656565"
            }
            onExited: {
                buttonColor = "#4b4b4b"
            }
            onClicked: {
                // cont.callPublish()
                btnDelegate.clicked()
            }
        }
    }
}
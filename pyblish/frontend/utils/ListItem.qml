import QtQuick 2.0
import QtQuick.Layouts 1.1


Item {
    id: listViewRoot
    
    width: 280
    height: 40

    ColumnLayout {
        id: ui
        width: parent.width
        height: parent.height
        spacing: 0
        Layout.alignment: Qt.AlignHCenter
        OuterBevelFrame {
            id: buttonFrame
            width: parent.width
            height: 40
            Text {
                id: instanceName
                // anchors.left: parent.left
                // anchors.verticalCenter: parent.verticalCenter
                // anchors.leftMargin: 5
                anchors.centerIn: parent
                text: modelData
                color: '#fefefe'
                font.family: 'Consolas'
            }
        } 
        OuterBevelFrame {
            id: extendRow
            visible: false
            width: parent.width
            height: 60
            Text {
                id: docText
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.leftMargin: 10
                anchors.topMargin: 10
                // anchors.centerIn: parent
                text: (
                    'Family: ' + list_families[index] + '\n' +
                    'Doc Name: ' + list_docNames[index] + '\n' +
                    'Doc Content: ' + list_docConts[index] + '\n'
                    )
                color: '#58b2f7'
                font.family: 'Consolas'
            }
        }
    }
    MouseArea {
        anchors.fill: parent
        onClicked: {
            // print(modelData)
            if(listViewRoot.height == 40){
                listViewRoot.height = 100
                extendRow.visible = true
            }
            else{
                listViewRoot.height = 40    
                extendRow.visible = false                       
            }
        }
    }
}
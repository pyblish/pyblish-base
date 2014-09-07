import QtQuick 2.0

import "../utils"

Item {
    id: root
    width: 200
    height: 200

    PButton {
    	anchors.centerIn: parent
    	iconVisibility: false
    	label: 'Publish'
    	height: 75
    	onClicked: cont.callPublish()
    }
}
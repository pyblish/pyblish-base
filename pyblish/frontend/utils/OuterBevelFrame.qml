import QtQuick 2.0

Item {
	id: outerBevel
	property color bgColor: "#4b4b4b"
	width: 500
	height: 500

	Rectangle {
		id: bg
		width: parent.width
		height: parent.height
		color: "#5d5d5d"
		Rectangle {
			width: parent.width-1
			height: parent.height-1
			anchors.right: parent.right
			anchors.bottom: parent.bottom
			color: "#3e3e3e"

			Rectangle {
				width: parent.width-1
				height: parent.height-1
				anchors.left: parent.left
				anchors.top: parent.top
				color: outerBevel.bgColor
			}
		}
	}
}
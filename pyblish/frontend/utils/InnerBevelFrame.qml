import QtQuick 2.0

Item {
	id: outerBevel
	width: 500
	height: 500

	Rectangle {
		id: bg
		width: parent.width
		height: parent.height
		color: "#252525"
		Rectangle {
			width: parent.width-1
			height: parent.height-1
			anchors.right: parent.right
			anchors.bottom: parent.bottom
			color: "#656565"

			Rectangle {
				width: parent.width-1
				height: parent.height-1
				anchors.left: parent.left
				anchors.top: parent.top
				color: "#323232"
			}
		}
	}
}
import QtQuick 2.0
import QtQuick.Controls 1.0
import QtQuick.Controls.Styles 1.0
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1
import Controller 1.0

import "../contents"
import "../utils"


ApplicationWindow {
	id: root
	width: 350
	height: 450
	title: "Pyblish"
	flags: Qt.FramelessWindowHint | Qt.Window | Qt.WindowStaysOnTopHint
	// maximumHeight: 500
	// maximumWidth: 700
	// minimumHeight: 500
	// minimumWidth: 700
	color: "transparent"
	// visible: false

	Item {
		id: main
		// visible: false
		anchors.centerIn: parent
		width: parent.width
		height: parent.height
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
				spacing: 1
				Layout.alignment: Qt.AlignHCenter | Qt.AlignHCenter
				RowLayout {
					id: header
					Layout.maximumHeight: 30
					Layout.maximumWidth: parent.width - 5
					Text {
						text: 'Pyblish'
						anchors.left: parent.left
						// anchors.top: parent.top
						anchors.right: parent.right
						// anchors.bottom: parent.bottom
						anchors.margins: 7
						color: 'white'
                    	font.family: 'Consolas'
                    	font.pixelSize: 13

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
					Layout.maximumHeight: parent.height-30
					Layout.alignment: Qt.AlignHCenter | Qt.AlignHCenter
					spacing: 0
					Content {

					}
				}
			}
		}
	}

	Controller {
		id: cont
	}
}
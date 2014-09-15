import QtQuick 2.0
import QtQuick.Controls 1.0
import QtQuick.Window 2.1
import QtQuick.Layouts 1.1

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
	Pyblish {}
}
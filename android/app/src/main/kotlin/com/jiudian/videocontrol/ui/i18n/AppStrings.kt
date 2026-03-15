package com.jiudian.videocontrol.ui.i18n

import androidx.compose.runtime.compositionLocalOf

/** All translatable strings for the app. */
data class AppStrings(
    // Connect Screen
    val appTitle: String,
    val remoteControl: String,
    val serverIpLabel: String,
    val portLabel: String,
    val connectButton: String,
    val connecting: String,
    val savedServers: String,
    val connectionFailed: String,
    val enterServerIp: String,

    // Control Screen
    val outputA: String,
    val outputB: String,
    val connected: String,
    val disconnected: String,
    val disconnect: String,
)

val ZhTwStrings = AppStrings(
    appTitle = "酒店影像控制系統",
    remoteControl = "遠端控制面板",
    serverIpLabel = "伺服器 IP 位址",
    portLabel = "連接埠",
    connectButton = "連線",
    connecting = "連線中…",
    savedServers = "已儲存的伺服器",
    connectionFailed = "連線失敗",
    enterServerIp = "請輸入伺服器 IP 位址",

    outputA = "輸出 A",
    outputB = "輸出 B",
    connected = "已連線",
    disconnected = "未連線",
    disconnect = "斷線",
)

val EnStrings = AppStrings(
    appTitle = "Video Control System",
    remoteControl = "Remote Control Panel",
    serverIpLabel = "Server IP Address",
    portLabel = "Port",
    connectButton = "Connect",
    connecting = "Connecting…",
    savedServers = "Saved Servers",
    connectionFailed = "Connection failed",
    enterServerIp = "Please enter server IP address",

    outputA = "Output A",
    outputB = "Output B",
    connected = "Connected",
    disconnected = "Disconnected",
    disconnect = "Disconnect",
)

fun stringsFor(lang: String): AppStrings = when (lang) {
    "en" -> EnStrings
    else -> ZhTwStrings
}

val LocalStrings = compositionLocalOf { ZhTwStrings }

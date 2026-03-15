package com.jiudian.videocontrol.data.api

import com.google.gson.Gson
import com.google.gson.JsonParser
import com.google.gson.reflect.TypeToken
import com.jiudian.videocontrol.domain.model.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import okhttp3.*
import java.util.concurrent.TimeUnit

class WebSocketClient {

    private val gson = Gson()
    private val client = OkHttpClient.Builder()
        .readTimeout(0, TimeUnit.MILLISECONDS)
        .pingInterval(15, TimeUnit.SECONDS)
        .build()

    private var webSocket: WebSocket? = null
    private var serverHost: String = ""
    private var serverPort: Int = 8080

    private val _serverState = MutableStateFlow(ServerState())
    val serverState: StateFlow<ServerState> = _serverState.asStateFlow()

    private val _isConnected = MutableStateFlow(false)
    val isConnected: StateFlow<Boolean> = _isConnected.asStateFlow()

    private var shouldReconnect = false

    fun connect(host: String, port: Int) {
        serverHost = host
        serverPort = port
        shouldReconnect = true
        doConnect()
    }

    private fun doConnect() {
        val url = "ws://$serverHost:$serverPort/ws/control"
        val request = Request.Builder().url(url).build()

        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                _isConnected.value = true
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                handleMessage(text)
            }

            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                webSocket.close(1000, null)
                _isConnected.value = false
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                _isConnected.value = false
                if (shouldReconnect) {
                    scheduleReconnect()
                }
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                _isConnected.value = false
                if (shouldReconnect) {
                    scheduleReconnect()
                }
            }
        })
    }

    private fun handleMessage(text: String) {
        try {
            // Parse via JsonElement to avoid Gson's Map<String,Any> Double-coercion
            // which turns integer fields (source_id: 0) into 0.0, breaking Int deserialization
            val root = JsonParser.parseString(text).asJsonObject
            val type = root.get("type")?.asString ?: return
            val data = root.get("data") ?: return

            when (type) {
                "state_sync" -> {
                    val state = gson.fromJson(data, ServerState::class.java)
                    _serverState.value = state
                }
                "status_update" -> {
                    val status = gson.fromJson(data, SystemStatus::class.java)
                    _serverState.value = _serverState.value.copy(status = status)
                }
                "input_update" -> {
                    val inputListType = object : TypeToken<List<Input>>() {}.type
                    val inputs: List<Input> = gson.fromJson(data, inputListType)
                    _serverState.value = _serverState.value.copy(inputs = inputs)
                }
                "scene_applied" -> {
                    // No longer used — output routing is handled via state_sync
                }
            }
        } catch (_: Exception) {
            // Ignore malformed messages
        }
    }

    fun sendCommand(type: String, data: Map<String, Any> = emptyMap()) {
        val message = mapOf("type" to type, "data" to data)
        webSocket?.send(gson.toJson(message))
    }

    fun applyScene(sceneId: String) {
        sendCommand("apply_scene", mapOf("scene_id" to sceneId))
    }

    fun switchInput(outputId: Int, inputId: Int) {
        sendCommand("switch_input", mapOf("output_id" to outputId, "input_id" to inputId))
    }

    fun setOutputInput(outputId: Int, inputId: Int) {
        val msg = mapOf("command" to "set_output_input", "output_id" to outputId, "input_id" to inputId)
        webSocket?.send(gson.toJson(msg))
    }

    private fun scheduleReconnect() {
        Thread {
            Thread.sleep(3000)
            if (shouldReconnect) {
                doConnect()
            }
        }.start()
    }

    fun disconnect() {
        shouldReconnect = false
        webSocket?.close(1000, "User disconnected")
        webSocket = null
        _isConnected.value = false
    }
}

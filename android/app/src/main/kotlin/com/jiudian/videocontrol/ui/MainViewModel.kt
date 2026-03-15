package com.jiudian.videocontrol.ui

import android.app.Application
import android.content.Context
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.jiudian.videocontrol.data.api.ServerRepository
import com.jiudian.videocontrol.domain.model.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

data class ConnectionConfig(val host: String, val port: Int) {
    val displayName: String get() = "$host:$port"
}

data class ConnectUiState(
    val host: String = "192.168.1.100",
    val port: String = "8080",
    val isConnecting: Boolean = false,
    val isAutoConnecting: Boolean = false,
    val error: String? = null,
    val savedServers: List<ConnectionConfig> = emptyList()
)

class MainViewModel(application: Application) : AndroidViewModel(application) {

    private val repository = ServerRepository()
    private val prefs = application.getSharedPreferences("jiudian_prefs", Context.MODE_PRIVATE)

    val serverState: StateFlow<ServerState> = repository.serverState
    val isConnected: StateFlow<Boolean> = repository.isConnected

    private val _connectState = MutableStateFlow(ConnectUiState())
    val connectState: StateFlow<ConnectUiState> = _connectState.asStateFlow()

    private val _language = MutableStateFlow("zh_tw")
    val language: StateFlow<String> = _language.asStateFlow()

    init {
        loadSavedServers()
        _language.value = prefs.getString("language", "zh_tw") ?: "zh_tw"
        attemptAutoConnect()
    }

    fun updateHost(host: String) {
        _connectState.update { it.copy(host = host, error = null) }
    }

    fun updatePort(port: String) {
        _connectState.update { it.copy(port = port, error = null) }
    }

    fun connect() {
        val state = _connectState.value
        val host = state.host.trim()
        val port = state.port.trim().toIntOrNull() ?: 8080

        if (host.isBlank()) {
            _connectState.update {
                it.copy(error = com.jiudian.videocontrol.ui.i18n.stringsFor(_language.value).enterServerIp)
            }
            return
        }

        _connectState.update { it.copy(isConnecting = true, error = null) }

        viewModelScope.launch {
            try {
                repository.connect(host, port)
                repository.getStatus()
                saveServer(host, port)
                _connectState.update { it.copy(isConnecting = false) }
            } catch (e: Exception) {
                kotlinx.coroutines.delay(2000)
                if (isConnected.value) {
                    saveServer(host, port)
                    _connectState.update { it.copy(isConnecting = false) }
                } else {
                    _connectState.update {
                        it.copy(
                            isConnecting = false,
                            error = "${com.jiudian.videocontrol.ui.i18n.stringsFor(_language.value).connectionFailed}: ${e.message}"
                        )
                    }
                    repository.disconnect()
                }
            }
        }
    }

    fun connectTo(config: ConnectionConfig) {
        _connectState.update { it.copy(host = config.host, port = config.port.toString()) }
        connect()
    }

    fun disconnect() {
        repository.disconnect()
        _connectState.update { it.copy(isConnecting = false, error = null) }
    }

    fun setOutputInput(outputId: Int, inputId: Int) {
        viewModelScope.launch {
            try {
                repository.setOutputInput(outputId, inputId)
            } catch (_: Exception) {
                repository.setOutputInputViaWs(outputId, inputId)
            }
        }
    }

    private fun attemptAutoConnect() {
        val lastHost = prefs.getString("last_connected_host", null) ?: return
        val lastPort = prefs.getInt("last_connected_port", -1)
        if (lastHost.isBlank() || lastPort < 0) return

        _connectState.update {
            it.copy(
                host = lastHost,
                port = lastPort.toString(),
                isAutoConnecting = true,
                isConnecting = true,
                error = null,
            )
        }

        viewModelScope.launch {
            try {
                repository.connect(lastHost, lastPort)
                repository.getStatus()
                _connectState.update { it.copy(isAutoConnecting = false, isConnecting = false) }
            } catch (e: Exception) {
                kotlinx.coroutines.delay(2000)
                if (isConnected.value) {
                    _connectState.update { it.copy(isAutoConnecting = false, isConnecting = false) }
                } else {
                    // Auto-connect failed — show normal screen with pre-filled fields
                    _connectState.update {
                        it.copy(isAutoConnecting = false, isConnecting = false, error = null)
                    }
                    repository.disconnect()
                }
            }
        }
    }

    private fun saveServer(host: String, port: Int) {
        val saved = _connectState.value.savedServers.toMutableList()
        val config = ConnectionConfig(host, port)
        saved.removeAll { it.host == host && it.port == port }
        saved.add(0, config)
        if (saved.size > 5) saved.removeLast()
        _connectState.update { it.copy(savedServers = saved) }
        prefs.edit()
            .putStringSet("saved_servers", saved.map { "${it.host}:${it.port}" }.toSet())
            .putString("last_connected_host", host)
            .putInt("last_connected_port", port)
            .apply()
    }

    private fun loadSavedServers() {
        val set = prefs.getStringSet("saved_servers", emptySet()) ?: emptySet()
        val servers = set.mapNotNull { entry ->
            val parts = entry.split(":")
            if (parts.size == 2) {
                ConnectionConfig(parts[0], parts[1].toIntOrNull() ?: 8080)
            } else null
        }
        _connectState.update { it.copy(savedServers = servers) }
    }

    override fun onCleared() {
        super.onCleared()
        repository.disconnect()
    }
}

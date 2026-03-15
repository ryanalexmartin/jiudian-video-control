package com.jiudian.videocontrol.domain.model

import com.google.gson.annotations.SerializedName

data class Input(
    val id: Int,
    val name: String,
    val status: String = "disconnected",
    val connected: Boolean = false,
    @SerializedName("preview_url") val previewUrl: String? = null
)

data class Output(
    val id: Int,
    val name: String,
    @SerializedName("source_type") val sourceType: String = "input",
    @SerializedName("source_id") val sourceId: Int = 0,
    val active: Boolean = false,
)

data class Layer(
    @SerializedName("input_id") val inputId: Int,
    val x: Int = 0,
    val y: Int = 0,
    val width: Int = 1920,
    val height: Int = 1080,
    @SerializedName("z_order") val zOrder: Int = 0,
    val alpha: Float = 1.0f,
    @SerializedName("border_width") val borderWidth: Int = 0,
    @SerializedName("border_color") val borderColor: String = "#00C8FF",
    val visible: Boolean = true
)

data class Scene(
    val id: String,
    val name: String,
    @SerializedName("layers") private val _layers: List<Layer>? = null,
    @SerializedName("background_color") val backgroundColor: String = "#0B0B1E",
    @SerializedName("is_default") val isDefault: Boolean = false
) {
    val layers: List<Layer> get() = _layers ?: emptyList()
}

data class SystemStatus(
    val fps: Float = 0f,
    val cpu: Float = 0f,
    val connections: Int = 0,
    val uptime: Float = 0f
)

data class ApplyResponse(
    val success: Boolean,
    val message: String = ""
)

data class SourceResponse(
    val success: Boolean,
    val message: String = ""
)

/** WebSocket message envelope */
data class WsMessage(
    val type: String,
    val data: Map<String, Any>? = null
)

/** State synced via WebSocket */
data class ServerState(
    val inputs: List<Input> = emptyList(),
    val outputs: List<Output> = emptyList(),
    val scenes: List<Scene> = emptyList(),
    val status: SystemStatus = SystemStatus()
)

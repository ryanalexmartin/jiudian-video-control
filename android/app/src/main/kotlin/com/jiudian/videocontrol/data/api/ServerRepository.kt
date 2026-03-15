package com.jiudian.videocontrol.data.api

import com.jiudian.videocontrol.domain.model.*
import kotlinx.coroutines.flow.StateFlow
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

class ServerRepository {

    private var api: JiudianApi? = null
    private val wsClient = WebSocketClient()

    val serverState: StateFlow<ServerState> = wsClient.serverState
    val isConnected: StateFlow<Boolean> = wsClient.isConnected

    private var currentHost: String = ""
    private var currentPort: Int = 8080

    fun connect(host: String, port: Int) {
        currentHost = host
        currentPort = port

        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BASIC
        }

        val httpClient = OkHttpClient.Builder()
            .connectTimeout(5, TimeUnit.SECONDS)
            .readTimeout(10, TimeUnit.SECONDS)
            .addInterceptor(logging)
            .build()

        api = Retrofit.Builder()
            .baseUrl("http://$host:$port")
            .client(httpClient)
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(JiudianApi::class.java)

        wsClient.connect(host, port)
    }

    fun disconnect() {
        wsClient.disconnect()
        api = null
    }

    private fun requireApi(): JiudianApi =
        api ?: throw IllegalStateException("Not connected to server")

    suspend fun getStatus(): SystemStatus =
        requireApi().getStatus()

    suspend fun getInputs(): List<Input> =
        requireApi().getInputs()

    suspend fun getOutputs(): List<Output> =
        requireApi().getOutputs()

    suspend fun getScenes(): List<Scene> =
        requireApi().getScenes()

    suspend fun applyScene(sceneId: String): ApplyResponse =
        requireApi().applyScene(sceneId)

    suspend fun setOutputSource(outputId: Int, sceneId: String): SourceResponse =
        requireApi().setOutputSource(outputId, mapOf("scene_id" to sceneId))

    fun applySceneViaWs(sceneId: String) {
        wsClient.applyScene(sceneId)
    }

    fun switchInputViaWs(outputId: Int, inputId: Int) {
        wsClient.switchInput(outputId, inputId)
    }

    suspend fun setOutputInput(outputId: Int, inputId: Int): SourceResponse =
        requireApi().setOutputSource(outputId, mapOf("source_type" to "input", "source_id" to inputId))

    fun setOutputInputViaWs(outputId: Int, inputId: Int) {
        wsClient.setOutputInput(outputId, inputId)
    }
}

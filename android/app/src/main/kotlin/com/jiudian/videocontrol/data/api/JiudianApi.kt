package com.jiudian.videocontrol.data.api

import com.jiudian.videocontrol.domain.model.*
import retrofit2.http.*

interface JiudianApi {

    @GET("/api/status")
    suspend fun getStatus(): SystemStatus

    @GET("/api/inputs")
    suspend fun getInputs(): List<Input>

    @GET("/api/outputs")
    suspend fun getOutputs(): List<Output>

    @GET("/api/scenes")
    suspend fun getScenes(): List<Scene>

    @POST("/api/scenes/{id}/apply")
    suspend fun applyScene(@Path("id") sceneId: String): ApplyResponse

    @POST("/api/outputs/{id}/source")
    suspend fun setOutputSource(
        @Path("id") outputId: Int,
        @Body body: Map<String, @JvmSuppressWildcards Any>
    ): SourceResponse
}

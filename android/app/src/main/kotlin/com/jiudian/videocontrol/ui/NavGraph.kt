package com.jiudian.videocontrol.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.*
import com.jiudian.videocontrol.ui.i18n.LocalStrings
import com.jiudian.videocontrol.ui.i18n.stringsFor
import com.jiudian.videocontrol.ui.screens.*
import com.jiudian.videocontrol.ui.theme.*

@Composable
fun JiudianApp(viewModel: MainViewModel = viewModel()) {
    val navController = rememberNavController()
    val isConnected by viewModel.isConnected.collectAsState()
    val connectState by viewModel.connectState.collectAsState()
    val serverState by viewModel.serverState.collectAsState()
    val language by viewModel.language.collectAsState()

    val strings = stringsFor(language)

    CompositionLocalProvider(LocalStrings provides strings) {
        LaunchedEffect(isConnected) {
            if (isConnected) {
                navController.navigate("control") {
                    popUpTo("connect") { inclusive = true }
                }
            }
        }

        Scaffold(containerColor = DarkBackground) { innerPadding ->
            NavHost(
                navController = navController,
                startDestination = "connect",
                modifier = Modifier
                    .fillMaxSize()
                    .padding(innerPadding)
                    .background(DarkBackground)
            ) {
                composable("connect") {
                    ConnectScreen(
                        state = connectState,
                        onHostChange = viewModel::updateHost,
                        onPortChange = viewModel::updatePort,
                        onConnect = viewModel::connect,
                        onConnectTo = viewModel::connectTo
                    )
                }

                composable("control") {
                    ControlScreen(
                        serverState = serverState,
                        onSetOutputInput = viewModel::setOutputInput,
                        onDisconnect = {
                            viewModel.disconnect()
                            navController.navigate("connect") {
                                popUpTo(0) { inclusive = true }
                            }
                        }
                    )
                }
            }
        }
    }
}

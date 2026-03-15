package com.jiudian.videocontrol.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Dns
import androidx.compose.material.icons.filled.Link
import androidx.compose.material.icons.filled.History
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.jiudian.videocontrol.ui.ConnectUiState
import com.jiudian.videocontrol.ui.ConnectionConfig
import com.jiudian.videocontrol.ui.components.GlassmorphicCard
import com.jiudian.videocontrol.ui.components.NeonButton
import com.jiudian.videocontrol.ui.i18n.LocalStrings
import com.jiudian.videocontrol.ui.theme.*

@Composable
fun ConnectScreen(
    state: ConnectUiState,
    onHostChange: (String) -> Unit,
    onPortChange: (String) -> Unit,
    onConnect: () -> Unit,
    onConnectTo: (ConnectionConfig) -> Unit
) {
    val s = LocalStrings.current

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(DarkBackground)
            .verticalScroll(rememberScrollState())
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Spacer(Modifier.height(48.dp))

        // Title
        Text(
            text = s.appTitle,
            style = MaterialTheme.typography.headlineLarge,
            color = NeonCyan,
            textAlign = TextAlign.Center
        )
        Spacer(Modifier.height(8.dp))
        Text(
            text = s.remoteControl,
            style = MaterialTheme.typography.bodyMedium,
            color = TextSecondary,
            textAlign = TextAlign.Center
        )

        Spacer(Modifier.height(48.dp))

        // Connection form
        GlassmorphicCard(
            modifier = Modifier.fillMaxWidth(),
            glowColor = NeonCyanDim
        ) {
            // IP Address
            Text(
                text = s.serverIpLabel,
                style = MaterialTheme.typography.labelLarge,
                color = TextSecondary
            )
            Spacer(Modifier.height(8.dp))
            OutlinedTextField(
                value = state.host,
                onValueChange = onHostChange,
                modifier = Modifier.fillMaxWidth(),
                placeholder = {
                    Text("192.168.1.100", color = TextSecondary.copy(alpha = 0.5f))
                },
                leadingIcon = {
                    Icon(Icons.Default.Dns, contentDescription = null, tint = NeonCyan)
                },
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Uri),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = NeonCyan,
                    unfocusedBorderColor = GlassBorder,
                    cursorColor = NeonCyan,
                    focusedTextColor = TextPrimary,
                    unfocusedTextColor = TextPrimary
                ),
                shape = RoundedCornerShape(10.dp)
            )

            Spacer(Modifier.height(16.dp))

            // Port
            Text(
                text = s.portLabel,
                style = MaterialTheme.typography.labelLarge,
                color = TextSecondary
            )
            Spacer(Modifier.height(8.dp))
            OutlinedTextField(
                value = state.port,
                onValueChange = onPortChange,
                modifier = Modifier.fillMaxWidth(),
                placeholder = { Text("8080", color = TextSecondary.copy(alpha = 0.5f)) },
                leadingIcon = {
                    Icon(Icons.Default.Link, contentDescription = null, tint = NeonCyan)
                },
                singleLine = true,
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = NeonCyan,
                    unfocusedBorderColor = GlassBorder,
                    cursorColor = NeonCyan,
                    focusedTextColor = TextPrimary,
                    unfocusedTextColor = TextPrimary
                ),
                shape = RoundedCornerShape(10.dp)
            )

            Spacer(Modifier.height(24.dp))

            // Error message
            if (state.error != null) {
                Text(
                    text = state.error,
                    style = MaterialTheme.typography.bodyMedium,
                    color = NeonRed,
                    modifier = Modifier.fillMaxWidth(),
                    textAlign = TextAlign.Center
                )
                Spacer(Modifier.height(12.dp))
            }

            // Connect button
            if (state.isConnecting) {
                Box(
                    modifier = Modifier.fillMaxWidth(),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator(
                        color = NeonCyan,
                        modifier = Modifier.size(36.dp),
                        strokeWidth = 3.dp
                    )
                }
                Spacer(Modifier.height(8.dp))
                Text(
                    text = if (state.isAutoConnecting) {
                        "${s.connecting} (${state.host}:${state.port})"
                    } else {
                        s.connecting
                    },
                    style = MaterialTheme.typography.bodyMedium,
                    color = NeonCyan,
                    modifier = Modifier.fillMaxWidth(),
                    textAlign = TextAlign.Center
                )
            } else {
                NeonButton(
                    text = s.connectButton,
                    onClick = onConnect,
                    modifier = Modifier.fillMaxWidth(),
                    icon = Icons.Default.Link
                )
            }
        }

        // Saved servers
        if (state.savedServers.isNotEmpty()) {
            Spacer(Modifier.height(32.dp))

            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.fillMaxWidth()
            ) {
                Icon(
                    Icons.Default.History,
                    contentDescription = null,
                    tint = TextSecondary,
                    modifier = Modifier.size(18.dp)
                )
                Spacer(Modifier.width(8.dp))
                Text(
                    text = s.savedServers,
                    style = MaterialTheme.typography.titleMedium,
                    color = TextSecondary
                )
            }

            Spacer(Modifier.height(12.dp))

            state.savedServers.forEach { config ->
                Surface(
                    onClick = { onConnectTo(config) },
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 4.dp),
                    shape = RoundedCornerShape(10.dp),
                    color = DarkSurface,
                    border = androidx.compose.foundation.BorderStroke(1.dp, GlassBorder)
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 16.dp, vertical = 12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            Icons.Default.Dns,
                            contentDescription = null,
                            tint = NeonCyan,
                            modifier = Modifier.size(18.dp)
                        )
                        Spacer(Modifier.width(12.dp))
                        Text(
                            text = config.displayName,
                            style = MaterialTheme.typography.bodyLarge,
                            color = TextPrimary
                        )
                    }
                }
            }
        }

        Spacer(Modifier.height(48.dp))
    }
}

package com.jiudian.videocontrol.ui.screens

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.jiudian.videocontrol.domain.model.ServerState
import com.jiudian.videocontrol.ui.i18n.LocalStrings
import com.jiudian.videocontrol.ui.theme.*

@Composable
fun ControlScreen(
    serverState: ServerState,
    onSetOutputInput: (outputId: Int, inputId: Int) -> Unit,
    onDisconnect: () -> Unit,
) {
    val s = LocalStrings.current

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(DarkBackground)
            .padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(24.dp)
    ) {
        // Header
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = s.appTitle,
                style = MaterialTheme.typography.headlineMedium,
                color = NeonCyan,
                fontWeight = FontWeight.Bold
            )
            OutlinedButton(
                onClick = onDisconnect,
                shape = RoundedCornerShape(8.dp),
                colors = ButtonDefaults.outlinedButtonColors(contentColor = Color(0xFFFF6666)),
                border = BorderStroke(1.dp, Color(0xFFFF6666))
            ) {
                Text(s.disconnect)
            }
        }

        Spacer(Modifier.height(8.dp))

        // Output A routing
        OutputRoutingSection(
            label = s.outputA,
            outputId = 0,
            activeInputId = getActiveInputId(serverState, 0),
            onSelectInput = onSetOutputInput,
        )

        // Output B routing
        OutputRoutingSection(
            label = s.outputB,
            outputId = 1,
            activeInputId = getActiveInputId(serverState, 1),
            onSelectInput = onSetOutputInput,
        )

        Spacer(Modifier.weight(1f))

        // Connection status
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.Center
        ) {
            Text(
                text = s.connected,
                color = Color(0xFF44FF44),
                style = MaterialTheme.typography.bodySmall
            )
        }
    }
}

@Composable
private fun OutputRoutingSection(
    label: String,
    outputId: Int,
    activeInputId: Int?,
    onSelectInput: (outputId: Int, inputId: Int) -> Unit,
) {
    Surface(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        color = DarkSurface,
        border = BorderStroke(1.dp, NeonCyan.copy(alpha = 0.3f))
    ) {
        Column(
            modifier = Modifier.padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Text(
                text = label,
                style = MaterialTheme.typography.titleLarge,
                color = NeonCyan,
                fontWeight = FontWeight.Bold
            )

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                for (inputId in 0..3) {
                    val isActive = activeInputId == inputId
                    InputSelectButton(
                        number = inputId + 1,
                        isActive = isActive,
                        onClick = { onSelectInput(outputId, inputId) },
                        modifier = Modifier.weight(1f)
                    )
                }
            }
        }
    }
}

@Composable
private fun InputSelectButton(
    number: Int,
    isActive: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
) {
    if (isActive) {
        Button(
            onClick = onClick,
            modifier = modifier.height(72.dp),
            shape = RoundedCornerShape(12.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = NeonCyan,
                contentColor = DarkBackground,
            ),
            elevation = ButtonDefaults.buttonElevation(defaultElevation = 8.dp)
        ) {
            Text(
                text = number.toString(),
                fontSize = 24.sp,
                fontWeight = FontWeight.Bold
            )
        }
    } else {
        OutlinedButton(
            onClick = onClick,
            modifier = modifier.height(72.dp),
            shape = RoundedCornerShape(12.dp),
            colors = ButtonDefaults.outlinedButtonColors(
                containerColor = DarkSurface,
                contentColor = NeonCyan,
            ),
            border = BorderStroke(1.dp, NeonCyan)
        ) {
            Text(
                text = number.toString(),
                fontSize = 24.sp,
                fontWeight = FontWeight.Bold
            )
        }
    }
}

/** Extract the active input ID for an output from server state. */
private fun getActiveInputId(state: ServerState, outputId: Int): Int? {
    val output = state.outputs.find { it.id == outputId } ?: return null
    if (output.sourceType == "input") {
        return output.sourceId
    }
    return null
}

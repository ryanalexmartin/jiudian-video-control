package com.jiudian.videocontrol.ui.components

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.shadow
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.jiudian.videocontrol.ui.theme.GlassBorder
import com.jiudian.videocontrol.ui.theme.GlassWhite

@Composable
fun GlassmorphicCard(
    modifier: Modifier = Modifier,
    glowColor: Color = Color.Transparent,
    cornerRadius: Dp = 12.dp,
    content: @Composable ColumnScope.() -> Unit
) {
    Surface(
        modifier = modifier
            .shadow(
                elevation = if (glowColor != Color.Transparent) 8.dp else 0.dp,
                shape = RoundedCornerShape(cornerRadius),
                ambientColor = glowColor,
                spotColor = glowColor
            ),
        shape = RoundedCornerShape(cornerRadius),
        color = GlassWhite,
        border = BorderStroke(1.dp, GlassBorder)
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            content = content
        )
    }
}

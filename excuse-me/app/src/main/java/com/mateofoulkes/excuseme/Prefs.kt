package com.mateofoulkes.excuseme

import android.content.Context

class Prefs(context: Context) {
    private val prefs = context.getSharedPreferences("excuse_me", Context.MODE_PRIVATE)

    var callerName: String
        get() = prefs.getString("caller_name", "Trabajo") ?: "Trabajo"
        set(value) = prefs.edit().putString("caller_name", value.ifBlank { "Trabajo" }).apply()

    var callerNumber: String
        get() = prefs.getString("caller_number", "5550100") ?: "5550100"
        set(value) = prefs.edit().putString("caller_number", value.ifBlank { "5550100" }).apply()

    var knockCount: Int
        get() = prefs.getInt("knock_count", 4)
        set(value) = prefs.edit().putInt("knock_count", value.coerceIn(2, 8)).apply()

    var delaySeconds: Int
        get() = prefs.getInt("delay_seconds", 10)
        set(value) = prefs.edit().putInt("delay_seconds", value.coerceIn(0, 30)).apply()

    var sensitivityLevel: Int
        get() = prefs.getInt("sensitivity_level", 1)
        set(value) = prefs.edit().putInt("sensitivity_level", value.coerceIn(0, 2)).apply()

    var armed: Boolean
        get() = prefs.getBoolean("armed", false)
        set(value) = prefs.edit().putBoolean("armed", value).apply()

    val impactThreshold: Float
        get() = when (sensitivityLevel) {
            0 -> 5.5f   // High sensitivity
            2 -> 11.5f  // Low sensitivity
            else -> 8.0f
        }
}

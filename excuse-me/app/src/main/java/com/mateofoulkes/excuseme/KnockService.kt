package com.mateofoulkes.excuseme

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.os.PowerManager
import android.os.SystemClock
import androidx.core.app.NotificationCompat
import kotlin.math.sqrt

class KnockService : Service(), SensorEventListener {

    companion object {
        const val ACTION_START = "com.mateofoulkes.excuseme.START"
        const val ACTION_STOP = "com.mateofoulkes.excuseme.STOP"
        private const val CHANNEL_ID = "armed"
        private const val NOTIFICATION_ID = 4104
        private const val MIN_IMPACT_GAP_MS = 140L
        private const val MAX_SEQUENCE_GAP_MS = 900L
    }

    private lateinit var sensorManager: SensorManager
    private var accelerometer: Sensor? = null
    private var wakeLock: PowerManager.WakeLock? = null
    private val handler = Handler(Looper.getMainLooper())
    private val gravity = FloatArray(3)
    private var gravityReady = false
    private var hits = 0
    private var lastImpactAt = 0L
    private var triggerScheduled = false

    override fun onCreate() {
        super.onCreate()
        sensorManager = getSystemService(SensorManager::class.java)
        accelerometer = sensorManager.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
        createChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_STOP -> stopListening()
            else -> startListening()
        }
        return START_NOT_STICKY
    }

    private fun startListening() {
        val prefs = Prefs(this)
        if (prefs.armed && !triggerScheduled) {
            // A duplicate start request should just refresh the foreground notification.
            showForegroundNotification()
            return
        }

        prefs.armed = true
        hits = 0
        lastImpactAt = 0L
        triggerScheduled = false
        gravityReady = false

        showForegroundNotification()

        val power = getSystemService(PowerManager::class.java)
        wakeLock = power.newWakeLock(
            PowerManager.PARTIAL_WAKE_LOCK,
            "ExcuseMe::KnockListening"
        ).apply { acquire() }

        accelerometer?.let {
            sensorManager.registerListener(this, it, SensorManager.SENSOR_DELAY_GAME)
        } ?: run {
            stopListening()
        }
    }

    private fun showForegroundNotification() {
        val prefs = Prefs(this)
        val stopIntent = Intent(this, KnockService::class.java).setAction(ACTION_STOP)
        val stopPendingIntent = PendingIntent.getService(
            this,
            2,
            stopIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        val openPendingIntent = PendingIntent.getActivity(
            this,
            3,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(R.drawable.ic_excuse_me)
            .setContentTitle(getString(R.string.armed_notification_title))
            .setContentText(
                getString(
                    R.string.armed_notification_text,
                    prefs.knockCount,
                    prefs.delaySeconds
                )
            )
            .setContentIntent(openPendingIntent)
            .setOngoing(true)
            .setSilent(true)
            .addAction(0, getString(R.string.disarm), stopPendingIntent)
            .build()

        if (Build.VERSION.SDK_INT >= 34) {
            startForeground(
                NOTIFICATION_ID,
                notification,
                ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE
            )
        } else {
            startForeground(NOTIFICATION_ID, notification)
        }
    }

    override fun onSensorChanged(event: SensorEvent) {
        if (triggerScheduled) return

        if (!gravityReady) {
            gravity[0] = event.values[0]
            gravity[1] = event.values[1]
            gravity[2] = event.values[2]
            gravityReady = true
            return
        }

        // Low-pass gravity estimate; what remains is a short impact / movement component.
        val alpha = 0.82f
        var linearSq = 0f
        for (i in 0..2) {
            gravity[i] = alpha * gravity[i] + (1f - alpha) * event.values[i]
            val linear = event.values[i] - gravity[i]
            linearSq += linear * linear
        }
        val impact = sqrt(linearSq)
        val threshold = Prefs(this).impactThreshold

        if (impact >= threshold) {
            registerImpact(SystemClock.elapsedRealtime())
        }
    }

    private fun registerImpact(now: Long) {
        if (now - lastImpactAt < MIN_IMPACT_GAP_MS) return

        if (lastImpactAt == 0L || now - lastImpactAt > MAX_SEQUENCE_GAP_MS) {
            hits = 0
        }

        lastImpactAt = now
        hits++

        val prefs = Prefs(this)
        if (hits >= prefs.knockCount) {
            triggerScheduled = true
            sensorManager.unregisterListener(this)
            val delayMs = prefs.delaySeconds * 1000L
            handler.postDelayed({
                CallController.triggerIncomingCall(this)
                stopListening()
            }, delayMs)
        }
    }

    override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) = Unit

    private fun stopListening() {
        handler.removeCallbacksAndMessages(null)
        sensorManager.unregisterListener(this)
        wakeLock?.let { if (it.isHeld) it.release() }
        wakeLock = null
        Prefs(this).armed = false
        triggerScheduled = false
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    override fun onDestroy() {
        sensorManager.unregisterListener(this)
        wakeLock?.let { if (it.isHeld) it.release() }
        wakeLock = null
        Prefs(this).armed = false
        super.onDestroy()
    }

    private fun createChannel() {
        val manager = getSystemService(NotificationManager::class.java)
        val channel = NotificationChannel(
            CHANNEL_ID,
            getString(R.string.armed_channel_name),
            NotificationManager.IMPORTANCE_LOW
        ).apply {
            description = getString(R.string.armed_channel_description)
            setSound(null, null)
        }
        manager.createNotificationChannel(channel)
    }

    override fun onBind(intent: Intent?): IBinder? = null
}

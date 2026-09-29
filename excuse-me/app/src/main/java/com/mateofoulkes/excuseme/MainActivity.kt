package com.mateofoulkes.excuseme

import android.Manifest
import android.app.Activity
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.provider.ContactsContract
import android.widget.ArrayAdapter
import android.widget.Button
import android.widget.EditText
import android.widget.SeekBar
import android.widget.Spinner
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat

class MainActivity : AppCompatActivity() {

    private lateinit var prefs: Prefs
    private lateinit var callerName: EditText
    private lateinit var callerNumber: EditText
    private lateinit var knockCount: SeekBar
    private lateinit var delay: SeekBar
    private lateinit var sensitivity: Spinner
    private lateinit var knockCountLabel: TextView
    private lateinit var delayLabel: TextView
    private lateinit var phoneAccountStatus: TextView
    private lateinit var armedStatus: TextView
    private lateinit var armButton: Button

    private val pickContact = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode != Activity.RESULT_OK) return@registerForActivityResult
        val uri = result.data?.data ?: return@registerForActivityResult
        contentResolver.query(
            uri,
            arrayOf(
                ContactsContract.CommonDataKinds.Phone.DISPLAY_NAME,
                ContactsContract.CommonDataKinds.Phone.NUMBER
            ),
            null,
            null,
            null
        )?.use { cursor ->
            if (cursor.moveToFirst()) {
                val name = cursor.getString(0).orEmpty()
                val number = cursor.getString(1).orEmpty()
                callerName.setText(name)
                callerNumber.setText(number)
                saveForm()
                Toast.makeText(this, R.string.contact_selected_hint, Toast.LENGTH_LONG).show()
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        prefs = Prefs(this)
        CallController.registerPhoneAccount(this)

        callerName = findViewById(R.id.callerName)
        callerNumber = findViewById(R.id.callerNumber)
        knockCount = findViewById(R.id.knockCount)
        delay = findViewById(R.id.delay)
        sensitivity = findViewById(R.id.sensitivity)
        knockCountLabel = findViewById(R.id.knockCountLabel)
        delayLabel = findViewById(R.id.delayLabel)
        phoneAccountStatus = findViewById(R.id.phoneAccountStatus)
        armedStatus = findViewById(R.id.armedStatus)
        armButton = findViewById(R.id.armButton)

        callerName.setText(prefs.callerName)
        callerNumber.setText(prefs.callerNumber)

        knockCount.min = 2
        knockCount.max = 8
        knockCount.progress = prefs.knockCount
        knockCountLabel.text = getString(R.string.knock_count_value, prefs.knockCount)
        knockCount.setOnSeekBarChangeListener(simpleSeekListener { value ->
            knockCountLabel.text = getString(R.string.knock_count_value, value)
        })

        delay.max = 30
        delay.progress = prefs.delaySeconds
        delayLabel.text = getString(R.string.delay_value, prefs.delaySeconds)
        delay.setOnSeekBarChangeListener(simpleSeekListener { value ->
            delayLabel.text = getString(R.string.delay_value, value)
        })

        ArrayAdapter.createFromResource(
            this,
            R.array.sensitivity_options,
            android.R.layout.simple_spinner_item
        ).also { adapter ->
            adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
            sensitivity.adapter = adapter
        }
        sensitivity.setSelection(prefs.sensitivityLevel)

        findViewById<Button>(R.id.pickContactButton).setOnClickListener {
            pickContact.launch(
                Intent(Intent.ACTION_PICK, ContactsContract.CommonDataKinds.Phone.CONTENT_URI)
            )
        }

        findViewById<Button>(R.id.phoneAccountButton).setOnClickListener {
            saveForm()
            CallController.registerPhoneAccount(this)
            CallController.openPhoneAccountSettings(this)
        }

        armButton.setOnClickListener {
            if (prefs.armed) disarm() else arm()
        }

        findViewById<Button>(R.id.testCallButton).setOnClickListener {
            saveForm()
            if (!CallController.triggerIncomingCall(this)) {
                Toast.makeText(this, R.string.enable_phone_account_first, Toast.LENGTH_LONG).show()
                CallController.openPhoneAccountSettings(this)
            }
        }

        requestNotificationPermissionIfNeeded()
    }

    override fun onResume() {
        super.onResume()
        refreshStatus()
    }

    private fun arm() {
        saveForm()
        CallController.registerPhoneAccount(this)
        if (!CallController.isPhoneAccountEnabled(this)) {
            Toast.makeText(this, R.string.enable_phone_account_first, Toast.LENGTH_LONG).show()
            CallController.openPhoneAccountSettings(this)
            return
        }

        val intent = Intent(this, KnockService::class.java).setAction(KnockService.ACTION_START)
        ContextCompat.startForegroundService(this, intent)
        prefs.armed = true
        refreshStatus()
    }

    private fun disarm() {
        startService(Intent(this, KnockService::class.java).setAction(KnockService.ACTION_STOP))
        prefs.armed = false
        refreshStatus()
    }

    private fun saveForm() {
        prefs.callerName = callerName.text.toString().trim()
        prefs.callerNumber = callerNumber.text.toString().trim()
        prefs.knockCount = knockCount.progress
        prefs.delaySeconds = delay.progress
        prefs.sensitivityLevel = sensitivity.selectedItemPosition
    }

    private fun refreshStatus() {
        val enabled = CallController.isPhoneAccountEnabled(this)
        phoneAccountStatus.text = if (enabled) {
            getString(R.string.phone_account_ready)
        } else {
            getString(R.string.phone_account_not_ready)
        }

        armedStatus.text = if (prefs.armed) {
            getString(R.string.armed_status)
        } else {
            getString(R.string.disarmed_status)
        }
        armButton.text = if (prefs.armed) getString(R.string.disarm) else getString(R.string.arm)
    }

    private fun requestNotificationPermissionIfNeeded() {
        if (
            Build.VERSION.SDK_INT >= 33 &&
            checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
        ) {
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 100)
        }
    }

    private fun simpleSeekListener(onChange: (Int) -> Unit) =
        object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(seekBar: SeekBar?, progress: Int, fromUser: Boolean) {
                onChange(progress)
            }
            override fun onStartTrackingTouch(seekBar: SeekBar?) = Unit
            override fun onStopTrackingTouch(seekBar: SeekBar?) = Unit
        }
}

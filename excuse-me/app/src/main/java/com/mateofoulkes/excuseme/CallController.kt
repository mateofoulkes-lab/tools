package com.mateofoulkes.excuseme

import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.telecom.PhoneAccount
import android.telecom.PhoneAccountHandle
import android.telecom.TelecomManager

object CallController {
    private const val ACCOUNT_ID = "excuse_me_incoming_v1"

    fun phoneAccountHandle(context: Context): PhoneAccountHandle = PhoneAccountHandle(
        ComponentName(context, ExcuseConnectionService::class.java),
        ACCOUNT_ID
    )

    fun registerPhoneAccount(context: Context) {
        val telecom = context.getSystemService(TelecomManager::class.java)
        val account = PhoneAccount.Builder(phoneAccountHandle(context), "Excuse Me")
            .setCapabilities(PhoneAccount.CAPABILITY_CALL_PROVIDER)
            .setShortDescription("Excuse Me")
            .setSupportedUriSchemes(listOf(PhoneAccount.SCHEME_TEL))
            .build()
        telecom.registerPhoneAccount(account)
    }

    fun isPhoneAccountEnabled(context: Context): Boolean {
        val telecom = context.getSystemService(TelecomManager::class.java)
        return telecom.getPhoneAccount(phoneAccountHandle(context))?.isEnabled == true
    }

    fun openPhoneAccountSettings(context: Context) {
        val intent = Intent(TelecomManager.ACTION_CHANGE_PHONE_ACCOUNTS)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(intent)
    }

    fun triggerIncomingCall(context: Context): Boolean {
        registerPhoneAccount(context)
        if (!isPhoneAccountEnabled(context)) return false

        val prefs = Prefs(context)
        val telecom = context.getSystemService(TelecomManager::class.java)
        val address = Uri.fromParts("tel", prefs.callerNumber, null)
        val extras = Bundle().apply {
            putParcelable(TelecomManager.EXTRA_INCOMING_CALL_ADDRESS, address)
        }

        return try {
            telecom.addNewIncomingCall(phoneAccountHandle(context), extras)
            true
        } catch (_: SecurityException) {
            false
        }
    }
}

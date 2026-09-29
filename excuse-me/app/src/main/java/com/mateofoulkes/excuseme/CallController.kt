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

    fun registerPhoneAccount(context: Context): Boolean {
        return try {
            val telecom = context.getSystemService(TelecomManager::class.java)
            val account = PhoneAccount.Builder(phoneAccountHandle(context), "Excuse Me")
                .setCapabilities(PhoneAccount.CAPABILITY_CALL_PROVIDER)
                .setShortDescription("Excuse Me")
                .setSupportedUriSchemes(listOf(PhoneAccount.SCHEME_TEL))
                .build()
            telecom.registerPhoneAccount(account)
            true
        } catch (_: SecurityException) {
            false
        } catch (_: IllegalArgumentException) {
            false
        }
    }

    /**
     * Returns true/false when Android lets us inspect our PhoneAccount.
     * On Android 12+ getPhoneAccount() can require READ_PHONE_NUMBERS even for
     * the app's own account. Excuse Me intentionally does not request that
     * privacy-sensitive permission just to paint a status label, so null means
     * "Android did not allow inspection" rather than "disabled".
     */
    fun isPhoneAccountEnabled(context: Context): Boolean? {
        return try {
            val telecom = context.getSystemService(TelecomManager::class.java)
            telecom.getPhoneAccount(phoneAccountHandle(context))?.isEnabled == true
        } catch (_: SecurityException) {
            null
        }
    }

    fun openPhoneAccountSettings(context: Context): Boolean {
        return try {
            val intent = Intent(TelecomManager.ACTION_CHANGE_PHONE_ACCOUNTS)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            context.startActivity(intent)
            true
        } catch (_: Exception) {
            false
        }
    }

    fun triggerIncomingCall(context: Context): Boolean {
        if (!registerPhoneAccount(context)) return false

        val prefs = Prefs(context)
        val telecom = context.getSystemService(TelecomManager::class.java)
        val address = Uri.fromParts("tel", prefs.callerNumber, null)
        val extras = Bundle().apply {
            putParcelable(TelecomManager.EXTRA_INCOMING_CALL_ADDRESS, address)
        }

        return try {
            // This call itself is the authoritative check: if the account is not
            // enabled, Telecom rejects it with SecurityException. No READ_PHONE_NUMBERS
            // permission is needed merely to launch Excuse Me.
            telecom.addNewIncomingCall(phoneAccountHandle(context), extras)
            true
        } catch (_: SecurityException) {
            false
        } catch (_: IllegalArgumentException) {
            false
        }
    }
}

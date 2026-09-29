package com.mateofoulkes.excuseme

import android.net.Uri
import android.telecom.Connection
import android.telecom.ConnectionRequest
import android.telecom.ConnectionService
import android.telecom.DisconnectCause
import android.telecom.PhoneAccountHandle
import android.telecom.TelecomManager

class ExcuseConnectionService : ConnectionService() {

    override fun onCreateIncomingConnection(
        connectionManagerPhoneAccount: PhoneAccountHandle?,
        request: ConnectionRequest
    ): Connection {
        val prefs = Prefs(this)
        val fallbackAddress = Uri.fromParts("tel", prefs.callerNumber, null)

        return ExcuseConnection().apply {
            setAddress(request.address ?: fallbackAddress, TelecomManager.PRESENTATION_ALLOWED)
            setCallerDisplayName(prefs.callerName, TelecomManager.PRESENTATION_ALLOWED)
            setConnectionCapabilities(Connection.CAPABILITY_MUTE)
            setAudioModeIsVoip(true)
            setRinging()
        }
    }

    override fun onCreateIncomingConnectionFailed(
        connectionManagerPhoneAccount: PhoneAccountHandle?,
        request: ConnectionRequest
    ) {
        super.onCreateIncomingConnectionFailed(connectionManagerPhoneAccount, request)
    }

    private class ExcuseConnection : Connection() {
        override fun onAnswer() {
            setActive()
        }

        override fun onAnswer(videoState: Int) {
            setActive()
        }

        override fun onReject() {
            finish(DisconnectCause.REJECTED)
        }

        override fun onReject(replyMessage: String?) {
            finish(DisconnectCause.REJECTED)
        }

        override fun onDisconnect() {
            finish(DisconnectCause.LOCAL)
        }

        override fun onAbort() {
            finish(DisconnectCause.CANCELED)
        }

        private fun finish(code: Int) {
            setDisconnected(DisconnectCause(code))
            destroy()
        }
    }
}

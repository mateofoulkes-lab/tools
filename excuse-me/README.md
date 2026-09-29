# Excuse Me

Native Android escape-call app.

## What it does

1. Configure the caller name/number (or pick an existing contact so the real Phone app can resolve its photo).
2. Configure 2–8 knocks, a 0–30 second delay and knock sensitivity.
3. Arm the app.
4. While the phone is in a pocket or the screen is off, a foreground service listens to the accelerometer.
5. After the configured knock sequence, the service waits the configured delay and reports a new incoming call to Android Telecom.
6. Android's **actual default Phone app** renders the incoming-call UI and handles ringtone, vibration, lock-screen UI, buttons and system language.

## Why Telecom instead of drawing a fake call screen?

A custom activity can only imitate Pixel/Samsung/Motorola call screens. Excuse Me registers a managed `ConnectionService` + `PhoneAccount`, then uses `TelecomManager.addNewIncomingCall()`. That lets the device's actual Phone app render the call.

## One-time setup

After installing:

1. Open **Excuse Me**.
2. Tap **Configure system call integration**.
3. Enable the **Excuse Me** calling account.
4. Return and use **Test call now**.
5. Set your knock count/delay and press **ARM**.

The app shows a low-priority foreground notification while armed. This is required for reliable continuous accelerometer access on modern Android.

## Caller photos

The exact OEM Phone UI owns contact lookup and avatar rendering. To get an exact photo, choose an existing Android contact from the app. For a fully invented caller name/number, the Phone app can show its normal unknown-caller avatar.

## Recents caveat

Managed Telecom calls are real calls from Android Telecom's point of view. Depending on the phone/dialer, a simulated call may appear in **Recents**. A future private mode could avoid the call log, but it would have to use a CallStyle/custom call surface instead of the OEM Phone screen.

## Build

Requirements:

- JDK 17
- Android SDK 36 / Build Tools 36.0.0
- Gradle 9.6.0

From this directory:

```bash
gradle :app:assembleDebug
```

The repository workflow **Build Excuse Me Android** also builds a debug APK and exposes it as a GitHub Actions artifact.

## Technical notes

- minSdk 26, targetSdk 36.
- AGP 9.4 with built-in Kotlin.
- Foreground service type: `specialUse` while explicitly armed.
- A partial wakelock is held only while armed so knock detection and the short configured delay remain responsive with the screen off.
- Knock detection uses a low-pass gravity estimate, linear acceleration magnitude, a 140 ms debounce and a 900 ms maximum gap between impacts.

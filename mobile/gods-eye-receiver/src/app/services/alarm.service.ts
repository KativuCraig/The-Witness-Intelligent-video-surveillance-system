import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { Capacitor } from '@capacitor/core';
import { Haptics } from '@capacitor/haptics';

/**
 * Loud in-app alarm: looping siren (Web Audio) + vibration on supported devices.
 * Stays on until the user taps Stop (browser autoplay rules may require a tap first).
 */
@Injectable({ providedIn: 'root' })
export class AlarmService {
  readonly ringing$ = new BehaviorSubject(false);

  private ctx: AudioContext | null = null;
  private osc: OscillatorNode | null = null;
  private gain: GainNode | null = null;
  private sirenInterval: ReturnType<typeof setInterval> | null = null;
  private vibrateInterval: ReturnType<typeof setInterval> | null = null;

  async start(): Promise<void> {
    if (this.ringing$.value) {
      return;
    }
    this.ringing$.next(true);
    await this.startSiren();
    this.startVibrationLoop();
  }

  stop(): void {
    if (!this.ringing$.value) {
      return;
    }
    this.ringing$.next(false);
    this.stopSiren();
    this.stopVibrationLoop();
  }

  private async startSiren(): Promise<void> {
    try {
      const Ctx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      this.ctx = new Ctx();
      if (this.ctx.state === 'suspended') {
        await this.ctx.resume();
      }
      this.gain = this.ctx.createGain();
      /* Louder siren; square wave is harsh — stay below ~0.85 to limit clipping */
      this.gain.gain.value = 0.72;
      this.osc = this.ctx.createOscillator();
      this.osc.type = 'square';
      this.osc.frequency.value = 880;
      this.osc.connect(this.gain);
      this.gain.connect(this.ctx.destination);
      this.osc.start();

      let high = true;
      this.sirenInterval = setInterval(() => {
        if (!this.osc || !this.ctx) {
          return;
        }
        high = !high;
        this.osc.frequency.setValueAtTime(high ? 920 : 520, this.ctx.currentTime);
      }, 180);
    } catch (e) {
      console.warn('[The Witness] Could not start alarm audio', e);
    }
  }

  private stopSiren(): void {
    if (this.sirenInterval) {
      clearInterval(this.sirenInterval);
      this.sirenInterval = null;
    }
    try {
      this.osc?.stop();
    } catch {
      /* already stopped */
    }
    this.osc?.disconnect();
    this.gain?.disconnect();
    void this.ctx?.close().catch(() => undefined);
    this.osc = null;
    this.gain = null;
    this.ctx = null;
  }

  private startVibrationLoop(): void {
    const pulse = (): void => {
      if (!this.ringing$.value) {
        return;
      }
      if (Capacitor.isNativePlatform()) {
        void Haptics.vibrate({ duration: 600 }).catch(() => undefined);
      } else if (typeof navigator !== 'undefined' && typeof navigator.vibrate === 'function') {
        navigator.vibrate([450, 100, 450]);
      }
    };
    pulse();
    this.vibrateInterval = setInterval(pulse, 700);
  }

  private stopVibrationLoop(): void {
    if (this.vibrateInterval) {
      clearInterval(this.vibrateInterval);
      this.vibrateInterval = null;
    }
    if (typeof navigator !== 'undefined' && typeof navigator.vibrate === 'function') {
      navigator.vibrate(0);
    }
  }
}

import { createClient } from '@supabase/supabase-js'

// Public values only (Vite `define` in vite.config.js): project URL + anon key.
// The service key never reaches the browser.
const URL = import.meta.env.VITE_SUPABASE_URL
const ANON = import.meta.env.VITE_SUPABASE_ANON_KEY

export const supabase = URL && ANON
  ? createClient(URL, ANON, { auth: { persistSession: true, autoRefreshToken: true, storageKey: 'sp_auth' } })
  : null

/** Current access token, or null (demo mode). */
export async function accessToken() {
  if (!supabase) return null
  const { data } = await supabase.auth.getSession()
  return data.session?.access_token || null
}

/** +91 and 10 digits, the format Supabase phone auth expects. */
export const toE164 = (digits) => `+91${digits}`

/** Friendly reason when Supabase cannot send the OTP. Never shows raw provider errors. */
export function otpError(error, t) {
  const msg = String(error?.message || error || '').toLowerCase()
  if (/provider|phone.*(disabled|not enabled)|unsupported phone/.test(msg)) {
    return { code: 'phone_off', text: t('Phone login is not switched on yet. You can continue in demo mode.', 'கைபேசி உள்நுழைவு இன்னும் இயக்கப்படவில்லை. டெமோ முறையில் தொடரலாம்.') }
  }
  if (/rate|too many|seconds/.test(msg)) return { code: 'rate', text: t('Please wait a minute before asking for another code.', 'ஒரு நிமிடம் காத்திருந்து மீண்டும் கேளுங்கள்.') }
  if (/expired|invalid|token/.test(msg)) return { code: 'bad_code', text: t('That code did not match. Check the SMS and try again.', 'குறியீடு பொருந்தவில்லை. மீண்டும் முயலுங்கள்.') }
  if (/verified|trial|unverified/.test(msg)) return { code: 'trial', text: t('This number is not verified on the demo SMS account yet.', 'இந்த எண் டெமோ SMS கணக்கில் சரிபார்க்கப்படவில்லை.') }
  return { code: 'other', text: t('Could not send the code right now. Try again or continue in demo mode.', 'இப்போது குறியீடு அனுப்ப முடியவில்லை.') }
}

import { createServerActionClient } from '@/lib/supabase/server'
import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const code = searchParams.get('code')
  const next = searchParams.get('next') ?? '/'

  if (code) {
    const supabase = await createServerActionClient()
    const { error } = await supabase.auth.exchangeCodeForSession(code)

    if (!error) {
      const forwardedHost = request.headers.get('x-forwarded-host')
      const proto = request.headers.get('x-forwarded-proto')
      const host = process.env.VERCEL_URL || (forwardedHost ?? request.headers.get('host'))
      const protocol = proto ?? 'https'

      return NextResponse.redirect(`${protocol}://${host}${next}`)
    }
  }

  return NextResponse.redirect(`${new URL(request.url).origin}/auth/login`)
}

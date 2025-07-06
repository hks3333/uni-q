import { Nunito } from 'next/font/google'
import './chat.css'
import ClientLayout from './client-layout'
import { AuthProvider } from '../contexts/AuthContext'

const nunito = Nunito({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-nunito',
  weight: ['400', '600', '700'],
})

export const metadata = {
  title: 'Uni-Q chat',
}

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={nunito.variable}>
      <body>
        <AuthProvider>
          <ClientLayout>{children}</ClientLayout>
        </AuthProvider>
      </body>
    </html>
  )
}

import { Link } from '@tanstack/react-router'
import { Factory, Mail, Phone, Linkedin, Twitter, Youtube } from 'lucide-react'

/**
 * Footer Component
 *
 * Site footer with navigation and legal:
 * - Single Responsibility: Footer navigation, legal, and contact info
 * - Design: Professional B2B with clear information architecture
 * - Links: Product, company, resources, legal sections
 */

const navigation = {
  product: [
    { name: 'Features', href: '#features' },
    { name: 'Pricing', href: '/pricing' },
    { name: 'Use Cases', href: '#use-cases' },
    { name: 'Integrations', href: '#integrations' },
    { name: 'Mobile Apps', href: '#mobile' },
  ],
  company: [
    { name: 'About Us', href: '#about' },
    { name: 'Careers', href: '#careers' },
    { name: 'Blog', href: '#blog' },
    { name: 'Case Studies', href: '#case-studies' },
    { name: 'Contact', href: '#contact' },
  ],
  resources: [
    { name: 'Documentation', href: '#docs' },
    { name: 'API Reference', href: '#api' },
    { name: 'Help Center', href: '#help' },
    { name: 'Video Tutorials', href: '#tutorials' },
    { name: 'Community Forum', href: '#forum' },
  ],
  legal: [
    { name: 'Privacy Policy', href: '#privacy' },
    { name: 'Terms of Service', href: '#terms' },
    { name: 'Security', href: '#security' },
    { name: 'Data Protection', href: '#data-protection' },
    { name: 'Compliance', href: '#compliance' },
  ],
}

const social = [
  {
    name: 'LinkedIn',
    href: '#',
    icon: Linkedin,
  },
  {
    name: 'Twitter',
    href: '#',
    icon: Twitter,
  },
  {
    name: 'YouTube',
    href: '#',
    icon: Youtube,
  },
]

export function Footer() {
  return (
    <footer className="border-t border-slate-200 bg-white" aria-labelledby="footer-heading">
      <h2 id="footer-heading" className="sr-only">
        Footer
      </h2>
      <div className="mx-auto max-w-7xl px-6 pb-8 pt-16 sm:pt-24 lg:px-8 lg:pt-32">
        <div className="xl:grid xl:grid-cols-3 xl:gap-8">
          {/* Brand Column */}
          <div className="space-y-8">
            <Link to="/" className="flex items-center gap-2">
              <Factory className="h-8 w-8 text-blue-600" />
              <span className="text-xl font-bold text-slate-900">Unison MES</span>
            </Link>
            <p className="text-sm leading-6 text-slate-600">
              Manufacturing ERP built for SME discrete manufacturers.
              Configure your shop floor in hours, not months.
            </p>
            {/* Social Links */}
            <div className="flex space-x-6">
              {social.map((item) => {
                const Icon = item.icon
                return (
                  <a
                    key={item.name}
                    href={item.href}
                    className="text-slate-400 transition-colors hover:text-slate-500"
                  >
                    <span className="sr-only">{item.name}</span>
                    <Icon className="h-6 w-6" />
                  </a>
                )
              })}
            </div>
          </div>

          {/* Navigation Columns */}
          <div className="mt-16 grid grid-cols-2 gap-8 xl:col-span-2 xl:mt-0">
            <div className="md:grid md:grid-cols-2 md:gap-8">
              <div>
                <h3 className="text-sm font-semibold leading-6 text-slate-900">Product</h3>
                <ul role="list" className="mt-6 space-y-4">
                  {navigation.product.map((item) => (
                    <li key={item.name}>
                      <a href={item.href} className="text-sm leading-6 text-slate-600 hover:text-slate-900">
                        {item.name}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="mt-10 md:mt-0">
                <h3 className="text-sm font-semibold leading-6 text-slate-900">Company</h3>
                <ul role="list" className="mt-6 space-y-4">
                  {navigation.company.map((item) => (
                    <li key={item.name}>
                      <a href={item.href} className="text-sm leading-6 text-slate-600 hover:text-slate-900">
                        {item.name}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
            <div className="md:grid md:grid-cols-2 md:gap-8">
              <div>
                <h3 className="text-sm font-semibold leading-6 text-slate-900">Resources</h3>
                <ul role="list" className="mt-6 space-y-4">
                  {navigation.resources.map((item) => (
                    <li key={item.name}>
                      <a href={item.href} className="text-sm leading-6 text-slate-600 hover:text-slate-900">
                        {item.name}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
              <div className="mt-10 md:mt-0">
                <h3 className="text-sm font-semibold leading-6 text-slate-900">Legal</h3>
                <ul role="list" className="mt-6 space-y-4">
                  {navigation.legal.map((item) => (
                    <li key={item.name}>
                      <a href={item.href} className="text-sm leading-6 text-slate-600 hover:text-slate-900">
                        {item.name}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Contact Information */}
        <div className="mt-16 border-t border-slate-200 pt-8">
          <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
            <div className="flex items-start gap-3">
              <Mail className="h-5 w-5 flex-shrink-0 text-slate-400" />
              <div>
                <p className="text-sm font-semibold text-slate-900">Email</p>
                <p className="mt-1 text-sm text-slate-600">sales@unisonmes.com</p>
                <p className="text-sm text-slate-600">support@unisonmes.com</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <Phone className="h-5 w-5 flex-shrink-0 text-slate-400" />
              <div>
                <p className="text-sm font-semibold text-slate-900">Phone</p>
                <p className="mt-1 text-sm text-slate-600">+91 80 1234 5678</p>
                <p className="text-sm text-slate-500">Mon-Fri, 9am-6pm IST</p>
              </div>
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-900">Industries We Serve</p>
              <p className="mt-1 text-sm text-slate-600">
                Automotive • Electronics • Switchgear • Industrial Equipment • Precision Manufacturing
              </p>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-8 border-t border-slate-200 pt-8 md:flex md:items-center md:justify-between">
          <p className="text-xs leading-5 text-slate-500">
            &copy; {new Date().getFullYear()} Unison Manufacturing ERP. All rights reserved.
          </p>
          <div className="mt-4 flex gap-6 md:mt-0">
            <a href="#privacy" className="text-xs text-slate-500 hover:text-slate-600">
              Privacy
            </a>
            <a href="#terms" className="text-xs text-slate-500 hover:text-slate-600">
              Terms
            </a>
            <a href="#security" className="text-xs text-slate-500 hover:text-slate-600">
              Security
            </a>
            <a href="#sitemap" className="text-xs text-slate-500 hover:text-slate-600">
              Sitemap
            </a>
          </div>
        </div>
      </div>
    </footer>
  )
}

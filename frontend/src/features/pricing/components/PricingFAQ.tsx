import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'

/**
 * Pricing FAQ Component
 *
 * Frequently asked questions about pricing:
 * - Single Responsibility: Display pricing FAQs
 * - Accordion for collapsible content
 * - Common pricing questions
 * - Clear, concise answers
 */

interface PricingFAQProps {
  className?: string
}

export function PricingFAQ({ className }: PricingFAQProps) {
  const faqs = [
    {
      question: 'What payment methods do you accept?',
      answer:
        'We accept all major credit cards (Visa, MasterCard, American Express), debit cards, and bank transfers. For Enterprise plans, we can arrange invoice-based billing with NET 30 payment terms. All transactions are processed securely through our payment partner.',
    },
    {
      question: 'Can I cancel my subscription anytime?',
      answer:
        'Yes, you can cancel your subscription at any time with no cancellation fees. If you cancel, you will continue to have access to your plan until the end of your current billing period. We also offer the option to pause your subscription for up to 3 months if you need a temporary break.',
    },
    {
      question: 'What happens after my free trial ends?',
      answer:
        'Your 14-day free trial gives you full access to all features in the Professional plan. At the end of the trial, you can choose to subscribe to any of our paid plans. If you don\'t subscribe, your account will be converted to a read-only mode for 30 days, giving you time to export your data. No credit card is required to start your trial.',
    },
    {
      question: 'Do you offer refunds?',
      answer:
        'Yes, we offer a 30-day money-back guarantee for all new subscriptions. If you\'re not satisfied with Unison MES within the first 30 days, contact our support team for a full refund. For annual subscriptions, we offer pro-rated refunds if you cancel within the first 90 days.',
    },
    {
      question: 'Can I upgrade or downgrade my plan?',
      answer:
        'Absolutely! You can upgrade or downgrade your plan at any time. When upgrading, you\'ll immediately get access to new features and any additional capacity. When downgrading, the change takes effect at the end of your current billing cycle. We\'ll prorate the charges so you only pay for what you use.',
    },
    {
      question: 'Is there a setup fee or implementation cost?',
      answer:
        'No, there are no setup fees for Starter and Professional plans. Our onboarding process is designed to be self-service, with guided tutorials and documentation. For Enterprise plans, we offer optional professional implementation services starting at $5,000, which includes dedicated onboarding, data migration, and custom training sessions.',
    },
    {
      question: 'What is included in support?',
      answer:
        'Starter plans include email support with 24-hour response time during business hours. Professional plans get priority support with 4-hour response time and access to our knowledge base and video tutorials. Enterprise customers receive dedicated support with a named success manager, 1-hour response time, and 24/7 emergency support for critical issues.',
    },
    {
      question: 'How do volume discounts work?',
      answer:
        'We offer automatic volume discounts based on the number of users: 10% off for 11-25 users, 15% off for 26-50 users, and 20% off for 51-100 users. For organizations with 100+ users, we provide custom pricing with additional discounts. Volume discounts apply automatically when you add users to your account.',
    },
    {
      question: 'What are the add-on costs?',
      answer:
        'Additional users cost $30/user/month, extra plants are $200/plant/month, and additional storage (per 10GB) is $50/month. These add-ons can be purchased at any time and are prorated based on your billing cycle. Enterprise customers can negotiate custom packages for large-scale add-ons.',
    },
    {
      question: 'Do annual plans really save 10%?',
      answer:
        'Yes! Annual billing gives you 10% off the monthly price. For example, the Professional plan costs $1,499/month (or $17,988/year) with monthly billing, but only $16,190/year with annual billing - saving you $1,798. You can switch to annual billing at any time, and we\'ll credit any payments made in the current billing cycle.',
    },
  ]

  return (
    <div className={className}>
      <Accordion type="single" collapsible className="w-full">
        {faqs.map((faq, index) => (
          <AccordionItem key={index} value={`item-${index}`}>
            <AccordionTrigger className="text-left text-lg font-semibold">
              {faq.question}
            </AccordionTrigger>
            <AccordionContent className="text-slate-600">
              {faq.answer}
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </div>
  )
}

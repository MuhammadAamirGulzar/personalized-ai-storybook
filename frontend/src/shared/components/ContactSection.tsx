'use client';

import React, { useState } from 'react';
import './ContactSection.css';

const ContactSection: React.FC = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    message: ''
  });
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>): void => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    setIsSubmitting(true);
    setSubmitStatus('idle');

    try {
      // Simulate form submission
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Here you would typically send the data to your backend
      console.log('Form submitted:', formData);

      setSubmitStatus('success');
      setFormData({ name: '', email: '', message: '' });
    } catch (error) {
      setSubmitStatus('error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section id="contact" className="contact-section">
      <div className="contact-container">
        <div className="section-header">
          <h2 className="section-title">Get in Touch</h2>
          <p className="section-description">
            Have questions about MyAIStorybook? We'd love to hear from you!
          </p>
        </div>

        <div className="contact-content">
          {/* Contact Form */}
          <div className="contact-form-container">
            <form className="contact-form" onSubmit={handleSubmit}>
              <div className="form-group">
                <label htmlFor="name" className="form-label">Name</label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  className="form-input"
                  placeholder="Your name"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="email" className="form-label">Email</label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  className="form-input"
                  placeholder="your.email@example.com"
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="message" className="form-label">Message</label>
                <textarea
                  id="message"
                  name="message"
                  value={formData.message}
                  onChange={handleInputChange}
                  className="form-textarea"
                  placeholder="Tell us about your experience or ask a question..."
                  rows={5}
                  required
                />
              </div>

              <button
                type="submit"
                className={`submit-button ${isSubmitting ? 'submitting' : ''}`}
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <span className="spinner"></span>
                    Sending...
                  </>
                ) : (
                  'Send Message'
                )}
              </button>

              {submitStatus === 'success' && (
                <div className="form-status success">
                  ✅ Thank you! Your message has been sent successfully.
                </div>
              )}

              {submitStatus === 'error' && (
                <div className="form-status error">
                  ❌ Sorry, there was an error sending your message. Please try again.
                </div>
              )}
            </form>
          </div>

          {/* Contact Information */}
          <div className="contact-info-container">
            <div className="contact-info-card">
              <h3 className="contact-info-title">Contact Information</h3>
              <div className="contact-info-list">
                <div className="contact-info-item">
                  <div className="contact-info-icon">📧</div>
                  <div className="contact-info-content">
                    <h4>Email</h4>
                    <p>contact@myaistorybook.com</p>
                  </div>
                </div>

                <div className="contact-info-item">
                  <div className="contact-info-icon">🏫</div>
                  <div className="contact-info-content">
                    <h4>Project Type</h4>
                    <p>Final Year Project</p>
                  </div>
                </div>

                <div className="contact-info-item">
                  <div className="contact-info-icon">🎓</div>
                  <div className="contact-info-content">
                    <h4>Institution</h4>
                    <p>FAST NUCES, Islamabad</p>
                  </div>
                </div>

                <div className="contact-info-item">
                  <div className="contact-info-icon">⚡</div>
                  <div className="contact-info-content">
                    <h4>Response Time</h4>
                    <p>Usually within 24 hours</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="contact-info-card">
              <h3 className="contact-info-title">Frequently Asked Questions</h3>
              <div className="faq-list">
                <div className="faq-item">
                  <h4 className="faq-question">How does the AI story generation work?</h4>
                  <p className="faq-answer">
                    Our system uses multiple AI agents working together to create stories,
                    generate illustrations, and ensure quality content.
                  </p>
                </div>

                <div className="faq-item">
                  <h4 className="faq-question">Is my data private?</h4>
                  <p className="faq-answer">
                    Yes! All processing happens locally on your device. We don't store
                    or share your personal information or story content.
                  </p>
                </div>

                <div className="faq-item">
                  <h4 className="faq-question">Can I customize the stories?</h4>
                  <p className="faq-answer">
                    Absolutely! You can provide detailed prompts to guide the story
                    creation process and influence the characters and plot.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default ContactSection;

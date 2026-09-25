import React, { useState } from 'react';
import { X, Sparkles, Award, ArrowRight, RotateCcw, Heart, Smile, Meh, HelpCircle, CheckCircle2 } from 'lucide-react';

export default function InteractiveActivityPlayer({ item, childId, onClose, onComplete }) {
  const [balance, setBalance] = useState(100);
  const [selectedChoices, setSelectedChoices] = useState([]);
  const [activeFeedback, setActiveFeedback] = useState(null);
  const [completed, setCompleted] = useState(false);
  const [reaction, setReaction] = useState(null);

  if (!item) return null;

  const payload = item.interactive_payload || {
    scenario: "Sparky has ₹100 from helping in the garden! What should he do?",
    starting_amount: 100,
    choices: [
      { id: "candy", text: "🍭 Spend ₹40 on colourful candy", cost: 40, reaction: "Yum! Sweet treat! But once eaten, the candy is gone.", badge_earned: "Sweet Tooth" },
      { id: "book", text: "📚 Buy a picture storybook for ₹30", cost: 30, reaction: "Awesome! You can read this book again and again with friends!", badge_earned: "Book Explorer" },
      { id: "piggy", text: "🐷 Put ₹50 into the golden piggy bank", cost: 50, reaction: "Clink! That ₹50 is safe for a rainy day or a future telescope!", badge_earned: "Master Saver" }
    ],
    lesson_takeaway: "Smart explorers divide their money: a little for fun, a little for learning, and a lot for the piggy bank!"
  };

  const handleSelectChoice = (choice) => {
    if (balance < choice.cost) {
      alert("You don't have enough coins left for this! Try another choice.");
      return;
    }
    const newBal = balance - choice.cost;
    setBalance(newBal);
    setSelectedChoices((prev) => [...prev, choice]);
    setActiveFeedback(choice);
  };

  const handleFinish = (userReaction) => {
    setReaction(userReaction);
    setCompleted(true);
    if (onComplete) {
      onComplete(item.id, userReaction);
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="kids-card" style={{ maxWidth: '640px', width: '100%', padding: '32px 28px', position: 'relative' }}>
        
        {/* Close Button */}
        <button
          onClick={onClose}
          style={{ position: 'absolute', top: '18px', right: '18px', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-muted)' }}
        >
          <X size={22} />
        </button>

        {/* Mascot & Coin Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '2.5rem' }}>🐿️</span>
            <div>
              <span className="kids-pill-badge" style={{ background: 'rgba(255, 209, 102, 0.25)', color: '#D97706' }}>
                Interactive Choice Game
              </span>
              <h2 style={{ fontSize: '1.4rem', fontWeight: 800, margin: '4px 0 0 0' }}>
                {item.title || "Sparky's ₹100 Money Adventure"}
              </h2>
            </div>
          </div>

          <div style={{
            background: 'linear-gradient(135deg, #FFD166 0%, #FFB703 100%)',
            padding: '8px 18px',
            borderRadius: '20px',
            fontWeight: 800,
            fontSize: '1.2rem',
            color: '#78350F',
            boxShadow: '0 4px 12px rgba(255, 183, 3, 0.35)',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            🪙 ₹{balance} left
          </div>
        </div>

        {/* Scenario Box */}
        <div style={{
          background: 'rgba(234, 231, 220, 0.4)',
          border: '2px solid #E2DED0',
          borderRadius: '20px',
          padding: '16px 20px',
          fontSize: '0.98rem',
          lineHeight: '1.5',
          marginBottom: '20px'
        }}>
          {payload.scenario}
        </div>

        {!completed ? (
          <>
            {/* Interactive Choices */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '22px' }}>
              {payload.choices.map((choice) => {
                const isPicked = selectedChoices.some(c => c.id === choice.id);
                return (
                  <button
                    key={choice.id}
                    onClick={() => handleSelectChoice(choice)}
                    disabled={balance < choice.cost}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '14px 20px',
                      borderRadius: '20px',
                      border: isPicked ? '3px solid #34BFA3' : '2px solid #E2DED0',
                      background: isPicked ? 'rgba(52, 191, 163, 0.1)' : 'var(--bg-main)',
                      cursor: balance >= choice.cost ? 'pointer' : 'not-allowed',
                      opacity: balance < choice.cost && !isPicked ? 0.5 : 1,
                      textAlign: 'left',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <span style={{ fontWeight: 700, fontSize: '1rem' }}>{choice.text}</span>
                    <span style={{
                      fontWeight: 800,
                      fontSize: '0.9rem',
                      background: '#FF7A59',
                      color: '#FFF',
                      padding: '4px 10px',
                      borderRadius: '12px'
                    }}>
                      -₹{choice.cost}
                    </span>
                  </button>
                );
              })}
            </div>

            {/* Active Feedback Box */}
            {activeFeedback && (
              <div style={{
                background: 'rgba(52, 191, 163, 0.12)',
                border: '2px solid #34BFA3',
                borderRadius: '18px',
                padding: '16px',
                marginBottom: '20px',
                animation: 'fadeIn 0.2s ease-out'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#0D9488', fontWeight: 800, marginBottom: '6px' }}>
                  <Sparkles size={18} /> Choice Result:
                </div>
                <p style={{ margin: 0, fontSize: '0.95rem', color: 'var(--text-primary)' }}>
                  {activeFeedback.reaction}
                </p>
                <div style={{ marginTop: '8px', fontSize: '0.85rem', fontWeight: 700, color: '#0D9488' }}>
                  🏆 Badge Unlocked: <strong>{activeFeedback.badge_earned}</strong>
                </div>
              </div>
            )}

            {/* Action Bar */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '2px solid #E2DED0', paddingTop: '18px' }}>
              <button
                onClick={() => { setBalance(100); setSelectedChoices([]); setActiveFeedback(null); }}
                style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.9rem' }}
              >
                <RotateCcw size={16} /> Reset Coins
              </button>

              <button
                onClick={() => handleFinish('loved')}
                className="kids-btn-fun"
                style={{ padding: '10px 24px', fontSize: '1rem' }}
              >
                Finish & Claim Stars ⭐
              </button>
            </div>
          </>
        ) : (
          /* Completion & Child Feedback Screen */
          <div style={{ textAlign: 'center', padding: '16px 0', animation: 'fadeIn 0.25s ease-out' }}>
            <div style={{ fontSize: '3.5rem', marginBottom: '10px' }}>🌟</div>
            <h3 style={{ fontSize: '1.4rem', fontWeight: 800, marginBottom: '8px', color: '#FF7A59' }}>
              Awesome Job, Explorer!
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', marginBottom: '20px', maxWidth: '420px', margin: '0 auto 20px auto' }}>
              {payload.lesson_takeaway}
            </p>

            <div style={{ background: 'rgba(255, 209, 102, 0.15)', borderRadius: '18px', padding: '16px', marginBottom: '24px' }}>
              <div style={{ fontWeight: 800, fontSize: '0.95rem', marginBottom: '12px' }}>
                How was this adventure?
              </div>
              <div style={{ display: 'flex', justifyContent: 'center', gap: '16px' }}>
                {[
                  { icon: '❤️', label: 'Loved it!', id: 'loved' },
                  { icon: '😊', label: 'Good', id: 'good' },
                  { icon: '😐', label: 'Okay', id: 'okay' },
                  { icon: '😕', label: 'Confused', id: 'confused' }
                ].map((r) => (
                  <button
                    key={r.id}
                    onClick={() => handleFinish(r.id)}
                    className="kids-reaction-btn"
                    style={{
                      border: reaction === r.id ? '3px solid #E85A4F' : '2px solid #E2DED0',
                      background: reaction === r.id ? 'rgba(232, 90, 79, 0.1)' : 'var(--bg-main)'
                    }}
                  >
                    <span>{r.icon}</span>
                    <span style={{ fontSize: '0.72rem', fontWeight: 700 }}>{r.label}</span>
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={onClose}
              className="kids-btn-fun"
              style={{ width: '100%', justifyContent: 'center' }}
            >
              Back to Today's Adventure 🚀
            </button>
          </div>
        )}

      </div>
    </div>
  );
}

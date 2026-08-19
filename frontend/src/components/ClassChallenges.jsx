import React, { useState, useEffect } from 'react';
import { Trophy, Flame, TrendingUp, Users, Target, ShieldCheck, Sparkles, Award, ArrowUpRight } from 'lucide-react';
import { fetchWeeklyChallenge, fetchClassLeaderboard, fetchMyPersonalGrowth } from '../services/api';

export default function ClassChallenges() {
  const [challenge, setChallenge] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [growth, setGrowth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadChallengeData = async () => {
    setLoading(true);
    setError('');
    try {
      const [chalData, lbData, growthData] = await Promise.all([
        fetchWeeklyChallenge(),
        fetchClassLeaderboard(),
        fetchMyPersonalGrowth().catch(() => null)
      ]);
      setChallenge(chalData);
      setLeaderboard(lbData);
      setGrowth(growthData);
    } catch (err) {
      setError('Unable to load class challenge statistics at this moment.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadChallengeData();
  }, []);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '80px 0', color: 'var(--text-secondary)' }}>
        <div className="spinner" style={{ margin: '0 auto 16px auto' }}></div>
        <p>Loading Class Challenge Leaderboard & Growth Metrics...</p>
      </div>
    );
  }

  const maxLeaderboardXp = leaderboard.length > 0 ? Math.max(...leaderboard.map(c => c.total_xp), 1000) : 1000;

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '24px 16px' }}>
      {/* Page Header */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
          <Trophy size={28} color="var(--accent-gold)" />
          <h1 style={{ fontSize: '1.8rem', fontWeight: 800 }}>Inter-Class Academic Challenges</h1>
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
          Learn and compete collaboratively with your class team! Individual effort boosts your collective class standing.
        </p>
      </div>

      {error && (
        <div style={{
          padding: '14px 18px',
          borderRadius: 'var(--radius-md)',
          background: 'hsla(346, 84%, 61%, 0.15)',
          border: '1px solid var(--accent-rose)',
          color: 'var(--accent-rose)',
          marginBottom: '24px'
        }}>
          {error}
        </div>
      )}

      {/* Active Weekly Challenge Banner */}
      {challenge && (
        <div className="glass-panel" style={{
          padding: '24px',
          marginBottom: '28px',
          background: 'linear-gradient(135deg, hsla(263, 70%, 58%, 0.12), hsla(186, 100%, 50%, 0.08))',
          border: '1px solid var(--border-glow)'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                <span style={{
                  padding: '4px 10px',
                  borderRadius: '12px',
                  background: 'var(--accent-gold)',
                  color: '#0a0f1d',
                  fontSize: '0.75rem',
                  fontWeight: 800,
                  textTransform: 'uppercase'
                }}>
                  🏆 Active Sprint
                </span>
                <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  Ends in {challenge.days_remaining} {challenge.days_remaining === 1 ? 'day' : 'days'}
                </span>
              </div>

              <h2 style={{ fontSize: '1.4rem', fontWeight: 800, marginBottom: '6px' }}>
                {challenge.title}
              </h2>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.92rem', maxWidth: '640px', lineHeight: 1.5, marginBottom: '12px' }}>
                {challenge.description}
              </p>

              <div style={{ display: 'flex', gap: '16px', fontSize: '0.86rem', color: 'var(--text-muted)' }}>
                <span>🎯 <strong>Subject:</strong> {challenge.subject_focus}</span>
                <span>📚 <strong>Focus Topic:</strong> {challenge.core_topic}</span>
              </div>
            </div>

            <div style={{
              padding: '16px 20px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--bg-card-solid)',
              border: '1px solid var(--border-subtle)',
              textAlign: 'center',
              minWidth: '160px'
            }}>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '4px', textTransform: 'uppercase' }}>
                Next Challenge
              </div>
              <div style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--accent-cyan)' }}>
                {challenge.next_challenge?.title}
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                Starts Monday
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Grid: Class Leaderboard (Left) & Private Personal Growth (Right) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px' }}>
        {/* Class Leaderboard */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Users size={20} color="var(--accent-cyan)" />
              <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Class Standings</h2>
            </div>
            <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
              🔒 Privacy-Safe Team Score
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
            {leaderboard.map((cls) => {
              const percentage = Math.min(100, Math.round((cls.total_xp / maxLeaderboardXp) * 100));
              return (
                <div
                  key={cls.class_id}
                  style={{
                    padding: '16px',
                    borderRadius: 'var(--radius-md)',
                    background: cls.is_my_class ? 'hsla(186, 100%, 50%, 0.08)' : 'var(--bg-space)',
                    border: cls.is_my_class ? '1px solid var(--accent-cyan)' : '1px solid var(--border-subtle)',
                    position: 'relative'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{
                        width: '26px',
                        height: '26px',
                        borderRadius: '50%',
                        background: cls.rank === 1 ? 'var(--accent-gold)' : (cls.rank === 2 ? 'var(--text-secondary)' : 'var(--bg-card-solid)'),
                        color: cls.rank === 1 ? '#0a0f1d' : 'var(--text-primary)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontSize: '0.82rem',
                        fontWeight: 800
                      }}>
                        #{cls.rank}
                      </span>
                      <strong style={{ fontSize: '1.05rem' }}>{cls.class_name}</strong>
                      {cls.is_my_class && (
                        <span style={{
                          fontSize: '0.7rem',
                          fontWeight: 700,
                          padding: '2px 8px',
                          borderRadius: '10px',
                          background: 'var(--accent-cyan)',
                          color: '#0a0f1d'
                        }}>
                          YOUR CLASS
                        </span>
                      )}
                    </div>

                    <div style={{ textAlign: 'right' }}>
                      <span style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>
                        {cls.total_xp}
                      </span>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginLeft: '4px' }}>XP</span>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div style={{
                    height: '10px',
                    borderRadius: '5px',
                    background: 'var(--bg-card-solid)',
                    overflow: 'hidden',
                    marginBottom: '8px'
                  }}>
                    <div style={{
                      height: '100%',
                      width: `${percentage}%`,
                      background: cls.is_my_class
                        ? 'linear-gradient(90deg, var(--accent-cyan), var(--accent-purple))'
                        : 'var(--accent-purple)',
                      borderRadius: '5px',
                      transition: 'width 0.6s ease'
                    }} />
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                    <span>👥 {cls.student_count} Active Students</span>
                    <span>⭐ {cls.average_accuracy}% Average Accuracy</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Private Personal Growth (Under-18 Safe) */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
              <TrendingUp size={20} color="var(--accent-emerald)" />
              <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Private Growth Tracker</h2>
            </div>

            <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', marginBottom: '20px', lineHeight: 1.5 }}>
              Edufeedia prioritizes <strong>individual improvement over popularity</strong>. Your detailed progress is private to you and your guardian.
            </p>

            {growth ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {/* Growth Pill */}
                <div style={{
                  padding: '16px',
                  borderRadius: 'var(--radius-md)',
                  background: 'hsla(160, 84%, 39%, 0.15)',
                  border: '1px solid var(--accent-emerald)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px'
                }}>
                  <Sparkles size={24} color="var(--accent-emerald)" />
                  <div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--accent-emerald)' }}>
                      +{growth.monthly_improvement_percentage}% Monthly Growth
                    </div>
                    <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                      {growth.growth_statement}
                    </div>
                  </div>
                </div>

                {/* Metric Cards */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  <div style={{
                    padding: '14px',
                    borderRadius: 'var(--radius-md)',
                    background: 'var(--bg-space)',
                    border: '1px solid var(--border-subtle)',
                    textAlign: 'center'
                  }}>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '4px' }}>My Quiz Accuracy</div>
                    <div style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>
                      {growth.average_accuracy}%
                    </div>
                  </div>

                  <div style={{
                    padding: '14px',
                    borderRadius: 'var(--radius-md)',
                    background: 'var(--bg-space)',
                    border: '1px solid var(--border-subtle)',
                    textAlign: 'center'
                  }}>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Class XP Contribution</div>
                    <div style={{ fontSize: '1.3rem', fontWeight: 800, color: 'var(--accent-gold)' }}>
                      {growth.current_xp} XP
                    </div>
                  </div>
                </div>

                <div style={{
                  padding: '14px',
                  borderRadius: 'var(--radius-md)',
                  background: 'var(--bg-space)',
                  border: '1px solid var(--border-subtle)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}>
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Active Streak</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 700, color: 'var(--accent-rose)' }}>
                    <Flame size={16} /> {growth.streak_days} Days Streak
                  </span>
                </div>
              </div>
            ) : (
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                Complete quizzes to populate your personal growth trajectory.
              </p>
            )}
          </div>

          <div style={{
            marginTop: '24px',
            padding: '12px 16px',
            borderRadius: 'var(--radius-md)',
            background: 'var(--bg-space)',
            border: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '0.8rem',
            color: 'var(--text-muted)'
          }}>
            <ShieldCheck size={16} color="var(--accent-emerald)" />
            <span>DPDP & COPPA compliant: Child data is protected and never ranked publicly.</span>
          </div>
        </div>
      </div>
    </div>
  );
}

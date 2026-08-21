import React, { useState } from 'react';
import { StyleSheet, Text, View, SafeAreaView, TouchableOpacity, ScrollView } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { Flame, CheckCircle2, XCircle, Lock, ArrowRight, RotateCcw, Share2 } from 'lucide-react-native';
import { MOCK_DAILY_PUZZLES } from './src/data/mockDailyPuzzles';

export default function App() {
  const puzzles = MOCK_DAILY_PUZZLES;
  const [currentIndex, setCurrentIndex] = useState(0);
  const [userAnswers, setUserAnswers] = useState([]);
  const [phase, setPhase] = useState('PLAYING'); // 'PLAYING' | 'REVEAL' | 'SUMMARY'
  const [streak, setStreak] = useState(5);

  const currentPuzzle = puzzles[currentIndex];

  const handleChoice = (action) => {
    setUserAnswers((prev) => [...prev, action]);
    setPhase('REVEAL');
  };

  const handleNext = () => {
    if (currentIndex + 1 < puzzles.length) {
      setCurrentIndex((prev) => prev + 1);
      setPhase('PLAYING');
    } else {
      setPhase('SUMMARY');
    }
  };

  const handleReset = () => {
    setCurrentIndex(0);
    setUserAnswers([]);
    setPhase('PLAYING');
  };

  const userAction = userAnswers[currentIndex];
  const isCorrect = userAction === currentPuzzle?.correctAction;
  const correctCount = userAnswers.filter((ans, idx) => ans === puzzles[idx]?.correctAction).length;

  return (
      <SafeAreaView style={styles.safeArea}>
        <StatusBar style="dark" />
        <View style={styles.container}>

          {/* Top Bar: Dots + Daily Badge + Streak */}
          <View style={styles.topNav}>
            <View style={styles.progressDots}>
              {puzzles.map((_, idx) => (
                  <View
                      key={idx}
                      style={[
                        styles.dot,
                        idx === currentIndex && styles.dotCurrent,
                        idx < userAnswers.length && (
                            userAnswers[idx] === puzzles[idx].correctAction ? styles.dotCorrect : styles.dotIncorrect
                        ),
                      ]}
                  />
              ))}
            </View>

            <View style={styles.badgeContainer}>
              <Text style={styles.badgeText}>Daily #{puzzles[0].puzzleNumber}</Text>
            </View>

            <View style={styles.streakBadge}>
              <Flame size={16} color="#F97316" />
              <Text style={styles.streakText}>{streak} Day</Text>
            </View>
          </View>

          {/* Active Puzzle Views (Playing & Reveal) */}
          {phase !== 'SUMMARY' && (
              <>
                {/* Ticker & Price */}
                <View style={styles.pairHeader}>
                  <View style={styles.pairDetails}>
                    <Text style={styles.pairTitle}>{currentPuzzle.pair}</Text>
                    <Text style={styles.timeframeText}>• {currentPuzzle.timeframe}</Text>
                  </View>
                  <Text style={styles.priceText}>
                    ${currentPuzzle.currentPrice.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </Text>
                </View>

                {/* Chart Area Box */}
                <View style={styles.chartCard}>
                  <Text style={styles.chartLabel}>Market Structure</Text>
                  <View style={styles.chartPlaceholder}>
                    <Text style={styles.placeholderSub}>[ Chart View Area ]</Text>
                    <Text style={styles.placeholderNote}>
                      {phase === 'REVEAL' ? 'Outcome revealed below.' : 'Analyze and pick direction.'}
                    </Text>
                  </View>
                </View>

                {/* Bottom Actions: Short/Long Buttons vs Analysis Card */}
                {phase === 'PLAYING' ? (
                    <View style={styles.decisionCard}>
                      <Text style={styles.promptText}>Will you SHORT or LONG?</Text>
                      <View style={styles.buttonRow}>
                        <TouchableOpacity
                            style={[styles.actionButton, styles.shortButton]}
                            activeOpacity={0.8}
                            onPress={() => handleChoice('SHORT')}
                        >
                          <Text style={styles.buttonTextShort}>SHORT</Text>
                        </TouchableOpacity>

                        <TouchableOpacity
                            style={[styles.actionButton, styles.longButton]}
                            activeOpacity={0.8}
                            onPress={() => handleChoice('LONG')}
                        >
                          <Text style={styles.buttonTextLong}>LONG</Text>
                        </TouchableOpacity>
                      </View>
                    </View>
                ) : (
                    <View style={styles.breakdownCard}>
                      <View style={styles.resultHeader}>
                        {isCorrect ? (
                            <View style={styles.resultBadgeGreen}>
                              <CheckCircle2 size={16} color="#166534" />
                              <Text style={styles.resultTextGreen}>Correct Call (+1)</Text>
                            </View>
                        ) : (
                            <View style={styles.resultBadgeRed}>
                              <XCircle size={16} color="#991B1B" />
                              <Text style={styles.resultTextRed}>Wrong Call</Text>
                            </View>
                        )}
                        <Text style={styles.correctLabel}>Target: {currentPuzzle.correctAction}</Text>
                      </View>

                      <Text style={styles.explanationText}>{currentPuzzle.explanation}</Text>

                      {/* Paywall Gate Demonstration */}
                      <View style={styles.deepDiveBox}>
                        {currentPuzzle.isPaywalled ? (
                            <View style={styles.paywallOverlay}>
                              <Lock size={16} color="#6B7280" />
                              <Text style={styles.paywallText}>Pro Tier: Deep Breakdown Locked</Text>
                            </View>
                        ) : (
                            <Text style={styles.deepAnalysisText}>{currentPuzzle.deepAnalysis}</Text>
                        )}
                      </View>

                      <TouchableOpacity style={styles.nextButton} activeOpacity={0.8} onPress={handleNext}>
                        <Text style={styles.nextButtonText}>
                          {currentIndex + 1 < puzzles.length ? 'Next Puzzle' : 'View Daily Score'}
                        </Text>
                        <ArrowRight size={18} color="#FFFFFF" />
                      </TouchableOpacity>
                    </View>
                )}
              </>
          )}

          {/* Daily Summary Screen */}
          {phase === 'SUMMARY' && (
              <ScrollView contentContainerStyle={styles.summaryContainer}>
                <View style={styles.summaryCard}>
                  <Text style={styles.summaryTitle}>Daily Round Completed</Text>
                  <Text style={styles.scoreText}>
                    {correctCount} / {puzzles.length}
                  </Text>
                  <Text style={styles.summarySub}>
                    {correctCount === 3 ? 'Perfect Read!' : correctCount >= 2 ? 'Solid Execution.' : 'Review the charts.'}
                  </Text>

                  {/* Result Grid */}
                  <View style={styles.shareGrid}>
                    {userAnswers.map((ans, idx) => (
                        <View
                            key={idx}
                            style={[
                              styles.shareBlock,
                              ans === puzzles[idx].correctAction ? styles.shareBlockGreen : styles.shareBlockRed,
                            ]}
                        >
                          <Text style={styles.shareBlockText}>{ans === puzzles[idx].correctAction ? '✓' : '✗'}</Text>
                        </View>
                    ))}
                  </View>

                  <TouchableOpacity style={styles.shareButton} activeOpacity={0.8}>
                    <Share2 size={18} color="#FFFFFF" />
                    <Text style={styles.shareButtonText}>Share Results</Text>
                  </TouchableOpacity>
                </View>

                {/* Pro Subscription CTA */}
                <View style={styles.proCard}>
                  <Text style={styles.proTitle}>Upgrade to Pro</Text>
                  <Text style={styles.proDesc}>
                    Unlock all deep technical breakdowns, archive puzzle access, and unlimited daily replays.
                  </Text>
                  <TouchableOpacity style={styles.proButton} activeOpacity={0.8}>
                    <Text style={styles.proButtonText}>Unlock All Puzzles</Text>
                  </TouchableOpacity>
                </View>

                <TouchableOpacity style={styles.replayButton} activeOpacity={0.8} onPress={handleReset}>
                  <RotateCcw size={16} color="#6B7280" />
                  <Text style={styles.replayText}>Replay Today's Set</Text>
                </TouchableOpacity>
              </ScrollView>
          )}

        </View>
      </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#F3F4F6',
  },
  container: {
    flex: 1,
    paddingHorizontal: 16,
    paddingBottom: 16,
    justifyContent: 'space-between',
  },
  topNav: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
  },
  progressDots: {
    flexDirection: 'row',
    gap: 6,
    padding: 8,
    borderWidth: 1.5,
    borderColor: '#1F2937',
    borderRadius: 12,
    backgroundColor: '#FFFFFF',
  },
  dot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#E5E7EB',
  },
  dotCurrent: {
    borderWidth: 1.5,
    borderColor: '#1F2937',
  },
  dotCorrect: {
    backgroundColor: '#22C55E',
  },
  dotIncorrect: {
    backgroundColor: '#EF4444',
  },
  badgeContainer: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderWidth: 1.5,
    borderColor: '#1F2937',
    borderRadius: 12,
    backgroundColor: '#FFFFFF',
  },
  badgeText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#1F2937',
  },
  streakBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderWidth: 1.5,
    borderColor: '#1F2937',
    borderRadius: 12,
    backgroundColor: '#FFFFFF',
  },
  streakText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#1F2937',
  },
  pairHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 4,
    marginBottom: 8,
  },
  pairDetails: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  pairTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#111827',
  },
  timeframeText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6B7280',
  },
  priceText: {
    fontSize: 18,
    fontWeight: '800',
    color: '#111827',
  },
  chartCard: {
    backgroundColor: '#FFFFFF',
    borderWidth: 2,
    borderColor: '#1F2937',
    borderRadius: 24,
    padding: 16,
    flex: 1,
    maxHeight: 340,
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  chartLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: '#9CA3AF',
    textTransform: 'uppercase',
  },
  chartPlaceholder: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F9FAFB',
    borderRadius: 16,
    borderWidth: 1,
    borderStyle: 'dashed',
    borderColor: '#D1D5DB',
    marginVertical: 8,
  },
  placeholderSub: {
    fontSize: 13,
    fontWeight: '700',
    color: '#6B7280',
  },
  placeholderNote: {
    fontSize: 11,
    color: '#9CA3AF',
    marginTop: 4,
  },
  decisionCard: {
    backgroundColor: '#FFFFFF',
    borderWidth: 2,
    borderColor: '#1F2937',
    borderRadius: 20,
    padding: 16,
    gap: 12,
  },
  promptText: {
    textAlign: 'center',
    fontSize: 15,
    fontWeight: '700',
    color: '#1F2937',
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 12,
  },
  actionButton: {
    flex: 1,
    height: 52,
    borderRadius: 14,
    borderWidth: 2,
    borderColor: '#1F2937',
    alignItems: 'center',
    justifyContent: 'center',
  },
  shortButton: {
    backgroundColor: '#FECACA',
  },
  longButton: {
    backgroundColor: '#BBF7D0',
  },
  buttonTextShort: {
    color: '#991B1B',
    fontWeight: '800',
    fontSize: 16,
  },
  buttonTextLong: {
    color: '#166534',
    fontWeight: '800',
    fontSize: 16,
  },
  breakdownCard: {
    backgroundColor: '#FFFFFF',
    borderWidth: 2,
    borderColor: '#1F2937',
    borderRadius: 20,
    padding: 16,
    gap: 10,
  },
  resultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  resultBadgeGreen: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  resultTextGreen: {
    color: '#166534',
    fontWeight: '700',
    fontSize: 12,
  },
  resultBadgeRed: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: '#FEE2E2',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  resultTextRed: {
    color: '#991B1B',
    fontWeight: '700',
    fontSize: 12,
  },
  correctLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: '#6B7280',
  },
  explanationText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#1F2937',
    lineHeight: 18,
  },
  deepDiveBox: {
    backgroundColor: '#F9FAFB',
    padding: 10,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  deepAnalysisText: {
    fontSize: 12,
    color: '#4B5563',
    lineHeight: 16,
  },
  paywallOverlay: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    justifyContent: 'center',
    paddingVertical: 4,
  },
  paywallText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#6B7280',
  },
  nextButton: {
    backgroundColor: '#111827',
    height: 48,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 4,
  },
  nextButtonText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 14,
  },
  summaryContainer: {
    flexGrow: 1,
    justifyContent: 'center',
    gap: 16,
    paddingVertical: 20,
  },
  summaryCard: {
    backgroundColor: '#FFFFFF',
    borderWidth: 2,
    borderColor: '#1F2937',
    borderRadius: 24,
    padding: 24,
    alignItems: 'center',
  },
  summaryTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#6B7280',
    textTransform: 'uppercase',
  },
  scoreText: {
    fontSize: 48,
    fontWeight: '900',
    color: '#111827',
    marginVertical: 4,
  },
  summarySub: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 16,
  },
  shareGrid: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 20,
  },
  shareBlock: {
    width: 48,
    height: 48,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: '#1F2937',
  },
  shareBlockGreen: {
    backgroundColor: '#BBF7D0',
  },
  shareBlockRed: {
    backgroundColor: '#FECACA',
  },
  shareBlockText: {
    fontSize: 18,
    fontWeight: '900',
    color: '#1F2937',
  },
  shareButton: {
    backgroundColor: '#111827',
    width: '100%',
    height: 48,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  shareButtonText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 15,
  },
  proCard: {
    backgroundColor: '#FEF3C7',
    borderWidth: 2,
    borderColor: '#B45309',
    borderRadius: 20,
    padding: 16,
    gap: 8,
  },
  proTitle: {
    fontSize: 16,
    fontWeight: '800',
    color: '#92400E',
  },
  proDesc: {
    fontSize: 12,
    color: '#78350F',
    lineHeight: 16,
  },
  proButton: {
    backgroundColor: '#B45309',
    height: 40,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 4,
  },
  proButtonText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 13,
  },
  replayButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 8,
  },
  replayText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6B7280',
  },
});
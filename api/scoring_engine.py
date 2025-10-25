"""
Comprehensive Mental Health Scoring Engine
Processes onboarding responses to generate insights and risk assessments
"""

import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime

class ScoringEngine:
    def __init__(self):
        # Response normalization mappings
        self.normalization_maps = {
            'sleep_quality': {
                'pretty_good': 4,
                'average': 3,
                'not_great': 2,
                'terrible': 1,
                'prefer_not_to_say': 3  # Default neutral
            },
            'energy_level': {
                'high': 5,
                'medium': 3,
                'low': 2,
                'drained': 1,
                'prefer_not_to_say': 3
            },
            'focus_level': {
                'sharp_as_usual': 5,
                'a_bit_off': 3,
                'very_hard': 1,
                'prefer_not_to_say': 3
            },
            'social_withdrawal': {
                'no': 5,
                'sometimes': 3,
                'quite_often': 2,
                'almost_always': 1,
                'prefer_not_to_say': 3
            },
            'appetite_change': {
                'normal': 4,
                'less': 2,
                'more': 3,
                'cant_tell': 3,
                'prefer_not_to_say': 3
            },
            'primary_affect': {
                'tired': 2,
                'okay': 3,
                'anxious': 2,
                'numb': 1,
                'overwhelmed': 1,
                'peaceful': 4,
                'motivated': 4,
                'sad': 2,
                'other': 3
            },
            'affect_duration': {
                'comes_and_goes': 3,
                'weeks': 2,
                'hard_to_tell': 3
            },
            'belief_safety': {
                'yes': 5,
                'sometimes': 3,
                'rarely': 1,
                'prefer_not_to_say': 3
            },
            'belief_trust': {
                'yes': 5,
                'depends': 3,
                'not_really': 1,
                'prefer_not_to_say': 3
            },
            'belief_control': {
                'mostly_yes': 5,
                'sometimes': 3,
                'not_much': 1,
                'prefer_not_to_say': 3
            },
            'belief_self': {
                'kind': 5,
                'depends': 3,
                'very_critical': 1,
                'prefer_not_to_say': 3
            },
            'belief_intimacy': {
                'easy': 5,
                'a_bit_hard': 3,
                'very_difficult': 1,
                'prefer_not_to_say': 3
            },
            'social_support': {
                'yes_definitely': 5,
                'maybe_one_or_two': 3,
                'not_really': 1,
                'prefer_not_to_say': 3
            }
        }
        
        # Domain weights for composite scoring
        self.domain_weights = {
            'mood_stability': 0.25,
            'energy_function': 0.20,
            'social_engagement': 0.20,
            'cognitive_flexibility': 0.20,
            'protective_strength': 0.15
        }
        
        # Field weights within domains
        self.field_weights = {
            'energy_function': {
                'sleep_quality': 1.2,
                'energy_level': 1.3,
                'focus_level': 1.0,
                'social_withdrawal': 1.4,
                'appetite_change': 1.0
            },
            'cognitive_flexibility': {
                'belief_safety': 1.2,
                'belief_trust': 1.0,
                'belief_control': 1.4,
                'belief_self': 1.4,
                'belief_intimacy': 1.2
            }
        }

    def normalize_responses(self, onboarding_data: Dict) -> Dict[str, float]:
        """Convert categorical responses to numeric scores (1-5 scale)"""
        normalized = {}
        
        # Direct mappings
        for field, mapping in self.normalization_maps.items():
            if field in onboarding_data and onboarding_data[field]:
                value = onboarding_data[field]
                if value in mapping:
                    normalized[field] = mapping[value]
                else:
                    normalized[field] = 3  # Default neutral
            else:
                normalized[field] = 3  # Default neutral
        
        # Handle special cases
        if 'coping_skills' in onboarding_data:
            coping_skills = onboarding_data['coping_skills']
            if isinstance(coping_skills, list):
                # More coping skills = higher score
                normalized['coping_skills_count'] = min(len(coping_skills), 5)
            else:
                normalized['coping_skills_count'] = 3
        
        return normalized

    def calculate_domain_scores(self, normalized: Dict[str, float]) -> Dict[str, float]:
        """Calculate domain scores from normalized field scores"""
        domain_scores = {}
        
        # Mood Stability (primary affect + emotion intensity + sleep)
        mood_fields = ['primary_affect', 'affect_duration', 'sleep_quality']
        mood_values = [normalized.get(field, 3) for field in mood_fields]
        domain_scores['mood_stability'] = (sum(mood_values) / len(mood_values)) * 20
        
        # Energy Function (weighted average)
        energy_fields = ['sleep_quality', 'energy_level', 'focus_level', 'social_withdrawal', 'appetite_change']
        energy_weights = [1.2, 1.3, 1.0, 1.4, 1.0]
        energy_values = [normalized.get(field, 3) for field in energy_fields]
        weighted_energy = sum(val * weight for val, weight in zip(energy_values, energy_weights))
        domain_scores['energy_function'] = (weighted_energy / sum(energy_weights)) * 20
        
        # Social Engagement (withdrawal + intimacy)
        social_fields = ['social_withdrawal', 'belief_intimacy']
        social_values = [normalized.get(field, 3) for field in social_fields]
        domain_scores['social_engagement'] = (sum(social_values) / len(social_values)) * 20
        
        # Cognitive Flexibility (belief systems)
        cognitive_fields = ['belief_trust', 'belief_control', 'belief_self']
        cognitive_values = [normalized.get(field, 3) for field in cognitive_fields]
        domain_scores['cognitive_flexibility'] = (sum(cognitive_values) / len(cognitive_values)) * 20
        
        # Protective Strength (support + coping + purpose)
        protective_fields = ['social_support', 'coping_skills_count']
        protective_values = [normalized.get(field, 3) for field in protective_fields]
        # Add purposeful activities if available
        if 'purposeful_activities' in normalized:
            protective_values.append(normalized['purposeful_activities'])
        domain_scores['protective_strength'] = (sum(protective_values) / len(protective_values)) * 20
        
        return domain_scores

    def calculate_mental_health_index(self, domain_scores: Dict[str, float]) -> float:
        """Calculate composite mental health index"""
        weighted_sum = 0
        for domain, score in domain_scores.items():
            weight = self.domain_weights.get(domain, 0.2)
            weighted_sum += score * weight
        
        return round(weighted_sum, 1)

    def determine_cluster(self, domain_scores: Dict[str, float], normalized: Dict[str, float]) -> Tuple[str, float]:
        """Determine primary emotional cluster and confidence"""
        clusters = {
            'cluster_affective_low': self._calculate_affective_low_score(domain_scores, normalized),
            'cluster_anxiety': self._calculate_anxiety_score(domain_scores, normalized),
            'cluster_burnout': self._calculate_burnout_score(domain_scores, normalized),
            'cluster_stress_overload': self._calculate_stress_overload_score(domain_scores, normalized),
            'cluster_resilient': self._calculate_resilient_score(domain_scores, normalized)
        }
        
        # Find cluster with highest score
        primary_cluster = max(clusters, key=clusters.get)
        confidence = min(clusters[primary_cluster], 1.0)  # Cap at 1.0
        
        return primary_cluster, round(confidence, 2)

    def _calculate_affective_low_score(self, domain_scores: Dict[str, float], normalized: Dict[str, float]) -> float:
        """Calculate affective low cluster score"""
        sleep_score = normalized.get('sleep_quality', 3)
        mood_score = normalized.get('primary_affect', 3)
        energy_score = normalized.get('energy_level', 3)
        
        # Low scores indicate higher likelihood
        score = (5 - sleep_score) * 0.3 + (5 - mood_score) * 0.4 + (5 - energy_score) * 0.3
        return score / 5  # Normalize to 0-1

    def _calculate_anxiety_score(self, domain_scores: Dict[str, float], normalized: Dict[str, float]) -> float:
        """Calculate anxiety cluster score"""
        control_score = normalized.get('belief_control', 3)
        safety_score = normalized.get('belief_safety', 3)
        focus_score = normalized.get('focus_level', 3)
        
        # Low control and safety, poor focus indicate anxiety
        score = (5 - control_score) * 0.4 + (5 - safety_score) * 0.3 + (5 - focus_score) * 0.3
        return score / 5

    def _calculate_burnout_score(self, domain_scores: Dict[str, float], normalized: Dict[str, float]) -> float:
        """Calculate burnout cluster score"""
        focus_score = normalized.get('focus_level', 3)
        energy_score = normalized.get('energy_level', 3)
        withdrawal_score = normalized.get('social_withdrawal', 3)
        
        # Low focus, energy, high withdrawal indicate burnout
        score = (5 - focus_score) * 0.4 + (5 - energy_score) * 0.4 + (5 - withdrawal_score) * 0.2
        return score / 5

    def _calculate_stress_overload_score(self, domain_scores: Dict[str, float], normalized: Dict[str, float]) -> float:
        """Calculate stress overload cluster score"""
        control_score = normalized.get('belief_control', 3)
        intimacy_score = normalized.get('belief_intimacy', 3)
        trust_score = normalized.get('belief_trust', 3)
        
        # Low control, intimacy, trust indicate stress overload
        score = (5 - control_score) * 0.4 + (5 - intimacy_score) * 0.3 + (5 - trust_score) * 0.3
        return score / 5

    def _calculate_resilient_score(self, domain_scores: Dict[str, float], normalized: Dict[str, float]) -> float:
        """Calculate resilient cluster score"""
        protective_score = domain_scores.get('protective_strength', 60)
        social_score = normalized.get('social_support', 3)
        coping_score = normalized.get('coping_skills_count', 3)
        
        # High protective factors indicate resilience
        score = (protective_score / 100) * 0.5 + (social_score / 5) * 0.3 + (coping_score / 5) * 0.2
        return score

    def assess_risk_flags(self, domain_scores: Dict[str, float], normalized: Dict[str, float], onboarding_data: Dict) -> Dict[str, any]:
        """Assess risk flags and priority levels"""
        flags = {
            'suicide_flag': False,
            'acute_risk_flag': False,
            'moderate_flag': False,
            'low_flag': False,
            'priority_level': 'stable'
        }
        
        # Suicide flag (immediate emergency)
        suicidal_thoughts = onboarding_data.get('suicidal_thoughts', 'no')
        if suicidal_thoughts in ['yes_briefly', 'yes_often']:
            flags['suicide_flag'] = True
            flags['priority_level'] = 'emergency'
            return flags
        
        # Acute risk (low mood + poor support)
        mood_stability = domain_scores.get('mood_stability', 60)
        social_support = normalized.get('social_support', 3)
        
        if mood_stability < 50 and social_support < 2:
            flags['acute_risk_flag'] = True
            flags['priority_level'] = 'high_risk'
        elif mood_stability < 50 and domain_scores.get('energy_function', 60) < 50:
            flags['moderate_flag'] = True
            flags['priority_level'] = 'moderate_risk'
        elif domain_scores.get('protective_strength', 60) > 70:
            flags['low_flag'] = True
            flags['priority_level'] = 'stable'
        
        return flags

    def generate_summary_text(self, cluster: str, domain_scores: Dict[str, float], risk_flags: Dict[str, any]) -> str:
        """Generate personalized summary text based on cluster and scores"""
        # Try to use AI-generated summary if available
        try:
            from simple_app import call_gemini
            
            # Create a prompt for AI summary generation with human-like tone
            prompt = f"""You are a caring, wise friend who has been following someone's mental health journey. Respond naturally and empathetically.

Assessment Results:
- Overall Pattern: {cluster}
- Mood Stability: {domain_scores.get('mood_stability', 0):.1f}/100
- Energy & Focus: {domain_scores.get('energy_function', 0):.1f}/100
- Social Connection: {domain_scores.get('social_engagement', 0):.1f}/100
- Mental Flexibility: {domain_scores.get('cognitive_flexibility', 0):.1f}/100
- Support Systems: {domain_scores.get('protective_strength', 0):.1f}/100
- Current Level: {risk_flags.get('priority_level', 'stable')}

Write a warm, human response that:
- Speaks to them like a trusted friend who understands
- Acknowledges their journey with genuine care
- Offers gentle, practical encouragement
- Uses natural, conversational language
- Avoids clinical or technical terms
- Feels like wisdom from someone who truly cares

Keep it brief (2-3 sentences) and focus on being supportive and understanding."""
            
            ai_summary = call_gemini(prompt)
            if ai_summary and ai_summary != "AI service not configured" and ai_summary != "AI service error":
                return ai_summary
        except Exception:
            pass
        
        # Fallback to static summaries if AI is not available
        summaries = {
            'cluster_affective_low': "You've been feeling low energy and emotionally fatigued. Journaling and short breaks may help balance your energy over the week.",
            'cluster_anxiety': "You might be feeling tense or worried lately. Breathing exercises and grounding techniques could help you feel more centered.",
            'cluster_burnout': "It sounds like you're feeling drained and overwhelmed. Taking small breaks and setting boundaries might help restore your energy.",
            'cluster_stress_overload': "You seem to be carrying a lot right now. Connecting with supportive people and practicing self-compassion could be helpful.",
            'cluster_resilient': "You have strong coping skills and support systems. Keep nurturing these relationships and practices that help you thrive."
        }
        
        base_summary = summaries.get(cluster, "Thank you for sharing your experiences. We're here to support your mental health journey.")
        
        # Add specific recommendations based on domain scores
        recommendations = []
        
        if domain_scores.get('sleep_quality', 60) < 50:
            recommendations.append("Consider establishing a consistent sleep routine.")
        
        if domain_scores.get('social_engagement', 60) < 50:
            recommendations.append("Staying connected with others can be really helpful.")
        
        if domain_scores.get('protective_strength', 60) > 70:
            recommendations.append("Your existing support systems are a great foundation.")
        
        if recommendations:
            base_summary += " " + " ".join(recommendations)
        
        return base_summary

    def process_onboarding_data(self, onboarding_data: Dict) -> Dict[str, any]:
        """Main processing function - converts onboarding data to insights"""
        try:
            # Step 1: Normalize responses
            normalized = self.normalize_responses(onboarding_data)
            
            # Step 2: Calculate domain scores
            domain_scores = self.calculate_domain_scores(normalized)
            
            # Step 3: Calculate mental health index
            mental_health_index = self.calculate_mental_health_index(domain_scores)
            
            # Step 4: Determine cluster
            cluster_primary, cluster_confidence = self.determine_cluster(domain_scores, normalized)
            
            # Step 5: Assess risk flags
            risk_flags = self.assess_risk_flags(domain_scores, normalized, onboarding_data)
            
            # Step 6: Generate summary
            summary_text = self.generate_summary_text(cluster_primary, domain_scores, risk_flags)
            
            # Step 7: Compile results
            results = {
                'mental_health_index': mental_health_index,
                'cluster_primary': cluster_primary,
                'cluster_confidence': cluster_confidence,
                'domain_scores': domain_scores,
                'risk_flags': risk_flags,
                'summary_text': summary_text,
                'emergency_mode': risk_flags.get('suicide_flag', False),
                'processed_at': datetime.now().isoformat()
            }
            
            return results
            
        except Exception as e:
            print(f"Error processing onboarding data: {e}")
            return {
                'error': 'Failed to process onboarding data',
                'mental_health_index': 50,
                'cluster_primary': 'cluster_resilient',
                'cluster_confidence': 0.5,
                'domain_scores': {},
                'risk_flags': {'priority_level': 'stable'},
                'summary_text': 'Thank you for completing the assessment.',
                'emergency_mode': False
            }

# Global scoring engine instance
scoring_engine = ScoringEngine()

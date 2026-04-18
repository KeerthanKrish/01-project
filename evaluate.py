"""
Evaluation script for marketplace detection system.
Measures accuracy, analyzes failure modes, and provides insights for improvement.
"""

import json
import sys
import os
from pathlib import Path
from collections import defaultdict
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.pipeline import create_pipeline
from src.tier1_detector import create_category_detector


def load_annotations(annotation_file):
    """
    Load ground truth annotations.
    
    Args:
        annotation_file: Path to JSON file with annotations
        
    Returns:
        List of (image_path, category, attributes) tuples
    """
    with open(annotation_file, 'r') as f:
        data = json.load(f)
    
    annotations = []
    for img_data in data.get('images', []):
        annotations.append({
            'path': img_data['filename'],
            'category': img_data['category'],
            'attributes': img_data.get('attributes', {})
        })
    
    return annotations


def evaluate_tier1(detector, test_data, top_k=3):
    """
    Evaluate Tier 1 category detection.
    
    Args:
        detector: CategoryDetector instance
        test_data: List of annotation dictionaries
        top_k: Consider prediction correct if in top-k
        
    Returns:
        Dictionary with evaluation metrics
    """
    print("="*70)
    print("TIER 1 EVALUATION - Category Detection")
    print("="*70)
    
    image_paths = [os.path.join('data/raw', item['path']) for item in test_data]
    true_labels = [item['category'] for item in test_data]
    
    # Get predictions
    print(f"\nProcessing {len(image_paths)} images...")
    predictions = detector.predict_batch(image_paths, top_k=top_k)
    
    # Calculate metrics
    correct_top1 = 0
    correct_topk = 0
    confusion_matrix = defaultdict(lambda: defaultdict(int))
    low_confidence_predictions = []
    
    for i, (pred, true_label) in enumerate(zip(predictions, true_labels)):
        pred_label = pred['category']
        confidence = pred['confidence']
        
        # Top-1 accuracy
        if pred_label == true_label:
            correct_top1 += 1
        
        # Top-k accuracy
        all_predictions = [pred_label] + [alt['label'] for alt in pred.get('alternatives', [])]
        if true_label in all_predictions[:top_k]:
            correct_topk += 1
        
        # Confusion matrix
        confusion_matrix[true_label][pred_label] += 1
        
        # Track low confidence predictions
        if confidence < 0.5:
            low_confidence_predictions.append({
                'image': image_paths[i],
                'true': true_label,
                'predicted': pred_label,
                'confidence': confidence
            })
    
    # Calculate metrics
    total = len(test_data)
    top1_accuracy = correct_top1 / total
    topk_accuracy = correct_topk / total
    
    # Print results
    print(f"\n{'='*70}")
    print("RESULTS")
    print(f"{'='*70}")
    print(f"Total images: {total}")
    print(f"Top-1 Accuracy: {top1_accuracy:.2%} ({correct_top1}/{total})")
    print(f"Top-{top_k} Accuracy: {topk_accuracy:.2%} ({correct_topk}/{total})")
    
    # Per-category accuracy
    print(f"\n{'='*70}")
    print("PER-CATEGORY ACCURACY")
    print(f"{'='*70}")
    
    category_stats = {}
    for true_cat in sorted(confusion_matrix.keys()):
        total_cat = sum(confusion_matrix[true_cat].values())
        correct_cat = confusion_matrix[true_cat][true_cat]
        accuracy_cat = correct_cat / total_cat if total_cat > 0 else 0
        category_stats[true_cat] = {
            'total': total_cat,
            'correct': correct_cat,
            'accuracy': accuracy_cat
        }
        print(f"{true_cat:30} {accuracy_cat:.1%} ({correct_cat}/{total_cat})")
    
    # Common misclassifications
    print(f"\n{'='*70}")
    print("COMMON MISCLASSIFICATIONS")
    print(f"{'='*70}")
    
    misclassifications = []
    for true_cat, pred_dict in confusion_matrix.items():
        for pred_cat, count in pred_dict.items():
            if true_cat != pred_cat and count > 0:
                misclassifications.append((true_cat, pred_cat, count))
    
    misclassifications.sort(key=lambda x: x[2], reverse=True)
    for true_cat, pred_cat, count in misclassifications[:10]:
        print(f"  {true_cat} → {pred_cat}: {count} times")
    
    # Low confidence predictions
    if low_confidence_predictions:
        print(f"\n{'='*70}")
        print(f"LOW CONFIDENCE PREDICTIONS ({len(low_confidence_predictions)})")
        print(f"{'='*70}")
        for item in low_confidence_predictions[:5]:
            print(f"  {Path(item['image']).name}")
            print(f"    True: {item['true']}, Predicted: {item['predicted']}")
            print(f"    Confidence: {item['confidence']:.2%}")
    
    return {
        'top1_accuracy': top1_accuracy,
        f'top{top_k}_accuracy': topk_accuracy,
        'total_images': total,
        'correct_top1': correct_top1,
        'category_stats': category_stats,
        'confusion_matrix': dict(confusion_matrix),
        'low_confidence_predictions': low_confidence_predictions
    }


def evaluate_pipeline(pipeline, test_data):
    """
    Evaluate end-to-end pipeline.
    
    Args:
        pipeline: MarketplaceDetectionPipeline instance
        test_data: List of annotation dictionaries
        
    Returns:
        Dictionary with evaluation metrics
    """
    print("\n" + "="*70)
    print("END-TO-END PIPELINE EVALUATION")
    print("="*70)
    
    results = []
    tier2_predictions = []
    
    print(f"\nProcessing {len(test_data)} images...")
    
    for item in test_data:
        image_path = os.path.join('data/raw', item['path'])
        
        try:
            result = pipeline.predict(image_path, return_metadata=True)
            results.append({
                'true_category': item['category'],
                'pred_category': result['tier1']['category'],
                'tier1_confidence': result['tier1']['confidence'],
                'has_tier2': bool(result['tier2'] and 'product_type' in result['tier2']),
                'tier2_result': result['tier2'] if result['tier2'] else {},
                'metadata': result['metadata']
            })
            
            # Track Tier 2 predictions
            if result['tier2'] and 'product_type' in result['tier2']:
                tier2_predictions.append({
                    'category': item['category'],
                    'tier2': result['tier2'],
                    'attributes': item['attributes']
                })
        
        except Exception as e:
            print(f"Error processing {image_path}: {e}")
    
    # Calculate metrics
    total = len(results)
    correct_tier1 = sum(1 for r in results if r['true_category'] == r['pred_category'])
    tier1_accuracy = correct_tier1 / total if total > 0 else 0
    
    # Tier 2 coverage
    tier2_coverage = sum(1 for r in results if r['has_tier2']) / total if total > 0 else 0
    
    # Average processing time
    avg_time = np.mean([r['metadata'].get('total_time_ms', 0) for r in results])
    
    # Average confidence
    avg_confidence = np.mean([r['tier1_confidence'] for r in results])
    
    print(f"\n{'='*70}")
    print("PIPELINE RESULTS")
    print(f"{'='*70}")
    print(f"Total images: {total}")
    print(f"Tier 1 Accuracy: {tier1_accuracy:.2%}")
    print(f"Tier 2 Coverage: {tier2_coverage:.1%} ({sum(1 for r in results if r['has_tier2'])}/{total})")
    print(f"Average Processing Time: {avg_time:.0f}ms")
    print(f"Average Confidence: {avg_confidence:.2%}")
    
    return {
        'total_images': total,
        'tier1_accuracy': tier1_accuracy,
        'tier2_coverage': tier2_coverage,
        'avg_processing_time_ms': avg_time,
        'avg_confidence': avg_confidence,
        'detailed_results': results
    }


def identify_failure_modes(evaluation_results):
    """
    Analyze evaluation results to identify common failure patterns.
    
    Args:
        evaluation_results: Dictionary from evaluate_tier1 or evaluate_pipeline
    """
    print("\n" + "="*70)
    print("FAILURE MODE ANALYSIS")
    print("="*70)
    
    # Check if we have detailed results
    if 'detailed_results' in evaluation_results:
        results = evaluation_results['detailed_results']
        
        # Analyze low confidence predictions
        low_conf = [r for r in results if r['tier1_confidence'] < 0.5]
        if low_conf:
            print(f"\n1. Low Confidence Predictions ({len(low_conf)})")
            print("   Potential causes: Poor image quality, ambiguous items, rare categories")
            print(f"   Recommendation: Review and improve image quality or add more training data")
        
        # Analyze Tier 2 coverage
        no_tier2 = [r for r in results if not r['has_tier2']]
        if no_tier2:
            print(f"\n2. Missing Tier 2 Detection ({len(no_tier2)})")
            print("   Some categories lack specialized detectors")
            print(f"   Recommendation: Implement Tier 2 detectors for popular categories")
    
    # Analyze category-specific issues
    if 'category_stats' in evaluation_results:
        weak_categories = [
            (cat, stats['accuracy']) 
            for cat, stats in evaluation_results['category_stats'].items()
            if stats['accuracy'] < 0.7
        ]
        
        if weak_categories:
            print(f"\n3. Weak Categories (< 70% accuracy)")
            for cat, acc in sorted(weak_categories, key=lambda x: x[1]):
                print(f"   - {cat}: {acc:.1%}")
            print("   Recommendation: Collect more examples or refine category definitions")
    
    # Recommendations
    print(f"\n{'='*70}")
    print("RECOMMENDATIONS")
    print(f"{'='*70}")
    print("1. Collect more data for weak categories")
    print("2. Implement additional Tier 2 detectors")
    print("3. Consider fine-tuning models on marketplace-specific data")
    print("4. Review and improve image preprocessing pipeline")
    print("5. Experiment with different confidence thresholds")


def main():
    """Main evaluation function."""
    print("="*70)
    print("MARKETPLACE DETECTION SYSTEM - EVALUATION")
    print("="*70)
    
    # Check for annotation file
    annotation_file = "data/annotations/labels.json"
    
    if not os.path.exists(annotation_file):
        print(f"\n❌ Annotation file not found: {annotation_file}")
        print("\n💡 To run evaluation:")
        print("   1. Collect test images (see DATA_COLLECTION.md)")
        print("   2. Create annotations file with ground truth labels")
        print("   3. Run this script again")
        print("\nFor now, running demo evaluation with synthetic data...")
        
        # Create synthetic test data
        from demo import create_sample_images
        samples = create_sample_images()
        
        # Create basic annotations
        test_data = [
            {'path': path.replace('data/raw/', ''), 'category': cat, 'attributes': {}}
            for path, cat in samples
        ]
    else:
        print(f"\n✓ Loading annotations from {annotation_file}")
        test_data = load_annotations(annotation_file)
        print(f"  Loaded {len(test_data)} annotated images")
    
    if not test_data:
        print("\n❌ No test data available")
        return
    
    # Initialize detectors
    print("\n" + "="*70)
    print("Initializing detection system...")
    print("="*70)
    
    try:
        # Tier 1 evaluation
        tier1_detector = create_category_detector()
        tier1_results = evaluate_tier1(tier1_detector, test_data, top_k=3)
        
        # Full pipeline evaluation
        pipeline = create_pipeline(confidence_threshold=0.5, enable_tier2=True)
        pipeline_results = evaluate_pipeline(pipeline, test_data)
        
        # Failure mode analysis
        identify_failure_modes(pipeline_results)
        
        # Save results
        output_dir = Path("data/processed")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        all_results = {
            'tier1': tier1_results,
            'pipeline': pipeline_results
        }
        
        output_file = output_dir / "evaluation_results.json"
        with open(output_file, 'w') as f:
            # Convert numpy types to native Python types
            json.dump(all_results, f, indent=2, default=float)
        
        print(f"\n💾 Results saved to: {output_file}")
        
        print("\n" + "="*70)
        print("EVALUATION COMPLETE!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Error during evaluation: {e}")
        print("\n💡 TIP: Make sure you have installed all requirements:")
        print("   pip install -r requirements.txt")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

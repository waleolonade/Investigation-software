use anyhow::{Context, Result};
use opencv::{imgcodecs, prelude::*};
use serde::{Deserialize, Serialize};
use std::env;
use std::io::{stdin, stdout, BufRead, Write};
use std::path::PathBuf;
use yolo_detector::YoloDetector;

#[derive(Serialize)]
struct BBox {
    x1: i32,
    y1: i32,
    x2: i32,
    y2: i32,
}

#[derive(Serialize)]
struct JsonDetection {
    class_id: usize,
    class_name: String,
    confidence: f32,
    bbox: BBox,
}

#[derive(Deserialize)]
struct LoopRequest {
    image: String,
    threshold: Option<f32>,
    nms: Option<f32>,
}

fn get_arg_value(args: &[String], key: &str) -> Option<String> {
    args.windows(2)
        .find_map(|pair| if pair[0] == key { Some(pair[1].clone()) } else { None })
}

fn has_flag(args: &[String], key: &str) -> bool {
    args.iter().any(|arg| arg == key)
}

fn print_usage(program: &str) {
    eprintln!(
        "Usage: {} --model <model.onnx> --names <classes.names> [--image <image.jpg>] [--threshold 0.5] [--nms 0.45] [--input-size 640] [--loop]",
        program
    );
}

fn run_loop(
    detector: &YoloDetector,
    default_threshold: f32,
    default_nms: f32,
) -> Result<()> {
    let stdin = stdin();
    let stdout = stdout();
    let reader = stdin.lock();
    let mut writer = stdout.lock();

    for line in reader.lines() {
        let line = line.context("Failed to read request line")?;
        let line = line.trim();
        if line.is_empty() {
            continue;
        }

        let request: LoopRequest = serde_json::from_str(line)
            .context("Failed to parse JSON request for Rust YOLO loop mode")?;

        let threshold = request.threshold.unwrap_or(default_threshold);
        let nms = request.nms.unwrap_or(default_nms);
        let image_path = request.image;

        let mat = imgcodecs::imread(&image_path, imgcodecs::IMREAD_COLOR)
            .context("Failed to read image")?;
        if mat.empty() {
            anyhow::bail!("Input image is empty or unreadable: {}", image_path);
        }

        let (detections, original_size) = detector
            .detect(&mat)
            .context("Detection failed")?;
        let parsed = detector.get_detections_with_scores(detections, threshold, nms, original_size);

        let output: Vec<JsonDetection> = parsed
            .into_iter()
            .map(|(class_id, class_name, rect, confidence)| JsonDetection {
                class_id,
                class_name,
                confidence,
                bbox: BBox {
                    x1: rect.x,
                    y1: rect.y,
                    x2: rect.x + rect.width,
                    y2: rect.y + rect.height,
                },
            })
            .collect();

        let json_text = serde_json::to_string(&output)
            .context("Failed to serialize detections")?;
        writeln!(writer, "{}", json_text).context("Failed to write loop output")?;
        writer.flush().context("Failed to flush loop output")?;
    }

    Ok(())
}

fn main() -> Result<()> {
    let args: Vec<String> = env::args().collect();
    let program = args.get(0).map(String::as_str).unwrap_or("yolo_detector");
    let loop_mode = has_flag(&args, "--loop");

    if args.len() < 7 && !loop_mode {
        print_usage(program);
        std::process::exit(2);
    }

    let model_path = get_arg_value(&args, "--model").context("Missing --model argument")?;
    let names_path = get_arg_value(&args, "--names").context("Missing --names argument")?;
    let threshold: f32 = get_arg_value(&args, "--threshold")
        .unwrap_or_else(|| "0.5".to_string())
        .parse()
        .context("Invalid threshold value")?;
    let nms: f32 = get_arg_value(&args, "--nms")
        .unwrap_or_else(|| "0.45".to_string())
        .parse()
        .context("Invalid nms value")?;
    let input_size: i32 = get_arg_value(&args, "--input-size")
        .unwrap_or_else(|| "640".to_string())
        .parse()
        .context("Invalid input-size value")?;

    let detector = YoloDetector::new(&model_path, &names_path, input_size)
        .context("Failed to initialize Rust YOLO detector")?;

    if loop_mode {
        return run_loop(&detector, threshold, nms);
    }

    let image_path = get_arg_value(&args, "--image").context("Missing --image argument")?;
    let mat = imgcodecs::imread(&image_path, imgcodecs::IMREAD_COLOR)
        .context("Failed to read image")?;
    if mat.empty() {
        anyhow::bail!("Input image is empty or unreadable: {}", image_path);
    }

    let (detections, original_size) = detector
        .detect(&mat)
        .context("Detection failed")?;
    let parsed = detector.get_detections_with_scores(detections, threshold, nms, original_size);

    let output: Vec<JsonDetection> = parsed
        .into_iter()
        .map(|(class_id, class_name, rect, confidence)| JsonDetection {
            class_id,
            class_name,
            confidence,
            bbox: BBox {
                x1: rect.x,
                y1: rect.y,
                x2: rect.x + rect.width,
                y2: rect.y + rect.height,
            },
        })
        .collect();

    let json_text = serde_json::to_string(&output).context("Failed to serialize detections")?;
    println!("{}", json_text);

    Ok(())
}

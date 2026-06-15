#[derive(Debug, Clone)]
pub struct CompletionRequest {
    pub prompt: String,
    pub preamble: Option<String>,
}


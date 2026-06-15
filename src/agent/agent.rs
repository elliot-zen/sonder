use crate::{CompletionModel, CompletionRequest};

#[derive(Debug, Clone)]
pub struct Agent<M> {
    pub(super) model: M,
    pub(super) preamble: Option<String>,
}

impl<M> Agent<M>
where
    M: CompletionModel,
{
    pub async fn prompt(&self, input: impl Into<String>) -> anyhow::Result<String> {
        let request = CompletionRequest {
            prompt: input.into(),
            preamble: self.preamble.clone(),
        };
        let response = self.model.completion(request).await?;
        Ok(response.text)
    }
}

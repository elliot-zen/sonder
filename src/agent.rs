use crate::completion::{CompletionModel, CompletionRequest};

#[derive(Debug, Clone)]
pub struct Agent<M> {
    model: M,
    preamble: Option<String>,
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

#[derive(Debug, Clone)]
pub struct AgentBuilder<M> {
    model: M,
    preamble: Option<String>,
}

impl<M> AgentBuilder<M>
where
    M: CompletionModel,
{
    pub fn new(model: M) -> Self {
        Self {
            model,
            preamble: None,
        }
    }

    pub fn preambel(mut self, preamble: impl Into<String>) -> Self {
        self.preamble = Some(preamble.into());
        self
    }

    pub fn build(self) -> Agent<M> {
        Agent {
            model: self.model,
            preamble: self.preamble,
        }
    }
}

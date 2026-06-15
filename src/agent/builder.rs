use crate::{Agent, CompletionModel};

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

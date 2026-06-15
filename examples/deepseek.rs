use sonder::{
    client::{CompletionClient, ProviderClient},
    providers::openai,
};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let client = openai::Client::from_env()?;
    let agent = client
        .agent("deepseek-v4-flash")
        .preambel("You are helpful!")
        .build();
    let response = agent.prompt("你好").await?;
    println!("{response}");
    Ok(())
}

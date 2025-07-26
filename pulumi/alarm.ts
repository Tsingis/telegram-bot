import * as aws from "@pulumi/aws";
import * as pulumi from "@pulumi/pulumi";

const config = new pulumi.Config();

const stack = pulumi.getStack();

if (stack === "test" || stack === "prod") {
  const emailRecipient = config.require("emailRecipient");

  const logGroupName = `/aws/lambda/telegram-bot-${stack}-webhook`;
  const snsTopicName = `telegram-bot-error-alarms-${stack}`;
  const alarmName = `telegram-bot-error-alarm-${stack}`;
  const metricName = `telegram-bot-error-metric-${stack}`;
  const metricNamespace = `Telegram-bot/Errors/${stack}`;
  const metricFilterPattern = '"ERROR:"';

  const topic = new aws.sns.Topic("errorTopic", {
    name: snsTopicName,
  });

  new aws.sns.TopicSubscription("emailSubscription", {
    topic: topic.arn,
    protocol: "email",
    endpoint: emailRecipient,
  });

  new aws.cloudwatch.LogMetricFilter("errorMetricFilter", {
    logGroupName,
    pattern: metricFilterPattern,
    metricTransformation: {
      name: metricName,
      namespace: metricNamespace,
      value: "1",
    },
  });

  new aws.cloudwatch.MetricAlarm("telegramErrorAlarm", {
    name: alarmName,
    alarmDescription: `Error alarm for Telegram bot ${stack}`,
    comparisonOperator: "GreaterThanThreshold",
    evaluationPeriods: 1,
    datapointsToAlarm: 1,
    metricName,
    namespace: metricNamespace,
    period: 60,
    statistic: "SampleCount",
    threshold: 0,
    treatMissingData: "missing",
    actionsEnabled: true,
    alarmActions: [topic.arn],
  });
}

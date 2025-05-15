import chalkTemplate from 'chalk-template';
import type { APIClient } from '../APIClient.js';
import type { IScenarioCommand, TestScenario } from '../TestScenario.js';

export interface IWaitPinParams {
  'part-id': string;
  pin: string;
  value: number;
  timeout?: number; // milliseconds, default: 5000
  interval?: number; // milliseconds, default: 100
}

const DEFAULT_TIMEOUT = 5000;
const DEFAULT_INTERVAL = 100;

export class WaitPinCommand implements IScenarioCommand {
  async run(scenario: TestScenario, client: APIClient, params: IWaitPinParams): Promise<void> {
    const partId = params['part-id'];
    const pinName = params.pin;
    const expectedValue = params.value;
    const timeout = params.timeout ?? DEFAULT_TIMEOUT;
    const interval = params.interval ?? DEFAULT_INTERVAL;
    const startTime = Date.now();

    scenario.log(
      chalkTemplate`wait-pin {yellow ${partId}}:{magenta ${pinName}} == {yellow ${expectedValue}} (timeout: ${timeout}ms)`,
    );

    return new Promise((resolve, reject) => {
      const checkPin = async () => {
        try {
          const pinInfo = await client.pinRead(partId, pinName);
          const currentValue = pinInfo?.value ? 1 : 0;

          if (currentValue === expectedValue) {
            scenario.log(
              chalkTemplate`WaitPin Success: {yellow ${partId}}:{magenta ${pinName}} is now {yellow ${currentValue}}`,
            );
            clearInterval(intervalId);
            clearTimeout(timeoutId);
            resolve();
          } else if (Date.now() - startTime > timeout) {
            scenario.fail(
              chalkTemplate`WaitPin Timeout: {yellow ${partId}}:{magenta ${pinName}} did not become {yellow ${expectedValue}} within ${timeout}ms. Last value: {red ${currentValue}}`,
            );
            clearInterval(intervalId);
            reject(new Error('WaitPin Timeout'));
          }
        } catch (error) {
          scenario.fail(
            chalkTemplate`WaitPin Error reading pin {yellow ${partId}}:{magenta ${pinName}}: ${(error as Error).message}`,
          );
          clearInterval(intervalId);
          clearTimeout(timeoutId);
          reject(error);
        }
      };

      const intervalId = setInterval(checkPin, interval);
      const timeoutId = setTimeout(() => {
        clearInterval(intervalId);
        scenario.fail(
            chalkTemplate`WaitPin Timeout: {yellow ${partId}}:{magenta ${pinName}} did not become {yellow ${expectedValue}} within ${timeout}ms.`,
        );
        reject(new Error('WaitPin Timeout'));
      }, timeout + interval);

      void checkPin();
    });
  }
}